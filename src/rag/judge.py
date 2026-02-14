"""RAG Judge: simulates a generative search engine with JSON structured output.

Receives retrieved document chunks and a question, produces a JSON answer
with structured citations. Replaces the fragile regex-based citation
extraction from the prototype.
See ADR-002 in docs/DECISIONS.md.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.prompts.registry import get_prompt

logger = logging.getLogger(__name__)

_REQUIRED_KEYS = ["answer", "citations", "sources_used", "sources_available_but_unused"]
_REQUIRED_CITATION_KEYS = ["index", "url", "quote"]


class RAGJudge:
    """Generates JSON answers with structured citations from retrieved context."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        if config is None:
            from src.config import load_experiment_config

            config = load_experiment_config()

        rag_config = config["rag_simulator"]
        prompt_spec = get_prompt("rag_judge")

        self.llm = ChatOpenAI(
            model=rag_config["model"],
            temperature=rag_config["temperature"],
            seed=rag_config.get("seed"),
            max_tokens=rag_config["max_tokens"],
            model_kwargs={"response_format": {"type": "json_object"}},
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", prompt_spec["system"]),
                ("human", prompt_spec["user_template"]),
            ]
        )

        self.token_usage: List[Dict[str, Any]] = []

    def generate_answer(
        self,
        question: str,
        retrieved_docs: List[Document],
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """Generate a JSON answer for *question* using *retrieved_docs* as context."""
        context = self._format_context(retrieved_docs)

        for attempt in range(max_retries + 1):
            try:
                messages = self.prompt.format_messages(
                    context=context, question=question
                )
                response = self.llm.invoke(messages)

                # Track token usage
                if hasattr(response, "response_metadata"):
                    usage = response.response_metadata.get("token_usage", {})
                    self.token_usage.append(
                        {"question": question[:80], "usage": usage}
                    )
                    logger.info(
                        "Tokens — prompt: %s, completion: %s",
                        usage.get("prompt_tokens", "?"),
                        usage.get("completion_tokens", "?"),
                    )

                result = json.loads(response.content)
                self._validate_schema(result)
                return result

            except json.JSONDecodeError as exc:
                logger.warning(
                    "JSON parse error (attempt %d/%d): %s",
                    attempt + 1,
                    max_retries + 1,
                    exc,
                )
                if attempt == max_retries:
                    raise

            except ValueError as exc:
                logger.warning(
                    "Schema validation error (attempt %d/%d): %s",
                    attempt + 1,
                    max_retries + 1,
                    exc,
                )
                if attempt == max_retries:
                    raise

        # Should not reach here, but just in case
        raise RuntimeError("generate_answer: all retries exhausted")

    # ------------------------------------------------------------------
    # Context formatting
    # ------------------------------------------------------------------

    def _format_context(self, docs: List[Document]) -> str:
        """Format retrieved chunks as structured markdown for the judge prompt."""
        sections = []
        for i, doc in enumerate(docs, 1):
            url = doc.metadata.get("source_url", "Unknown")
            title = doc.metadata.get("title", "")

            header = f"## [Fuente {i}: {url}]"
            if title:
                header += f"\n### Titulo: {title}"
            header += f"\n\n{doc.page_content}"
            sections.append(header)

        return "\n\n---\n\n".join(sections)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_schema(result: dict) -> None:
        """Raise ValueError if *result* doesn't match the expected JSON schema."""
        missing = [k for k in _REQUIRED_KEYS if k not in result]
        if missing:
            raise ValueError(f"Missing required keys: {missing}")

        for citation in result.get("citations", []):
            missing_c = [k for k in _REQUIRED_CITATION_KEYS if k not in citation]
            if missing_c:
                raise ValueError(
                    f"Citation {citation} missing keys: {missing_c}"
                )

    # ------------------------------------------------------------------
    # Cost tracking
    # ------------------------------------------------------------------

    def get_token_usage_summary(self) -> Dict[str, Any]:
        """Return aggregated token usage across all calls."""
        if not self.token_usage:
            return {"total_calls": 0}

        total_prompt = sum(
            u["usage"].get("prompt_tokens", 0) for u in self.token_usage
        )
        total_completion = sum(
            u["usage"].get("completion_tokens", 0) for u in self.token_usage
        )

        return {
            "total_calls": len(self.token_usage),
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_prompt + total_completion,
        }