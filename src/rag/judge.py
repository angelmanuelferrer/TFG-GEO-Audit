"""RAG Judge: simulates a generative search engine with JSON structured output.

Supports two modes:
- **classic**: Receives pre-retrieved chunks and generates a JSON answer (legacy).
- **agent**: Uses a FAISS search tool — the LLM decides what to search and how
  many times, then produces the JSON answer. More realistic simulation.

See ADR-002 and ADR-012 in docs/DECISIONS.md.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

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

        self._config = config
        rag_config = config["rag_simulator"]
        self._mode = rag_config.get("mode", "classic")

        self._init_llm(rag_config)
        self._init_prompts()

        self.token_usage: List[Dict[str, Any]] = []

    def _init_llm(self, rag_config: Dict[str, Any]) -> None:
        """Initialize the LLM based on model provider."""
        model = rag_config["model"]

        if model.startswith("gemini"):
            from langchain_google_genai import ChatGoogleGenerativeAI

            self.llm = ChatGoogleGenerativeAI(
                model=model,
                temperature=rag_config["temperature"],
                max_output_tokens=rag_config["max_tokens"],
            )
        else:
            from langchain_openai import ChatOpenAI

            self.llm = ChatOpenAI(
                model=model,
                temperature=rag_config["temperature"],
                seed=rag_config.get("seed"),
                max_tokens=rag_config["max_tokens"],
                model_kwargs={"response_format": {"type": "json_object"}},
            )

    def _init_prompts(self) -> None:
        """Load prompts for classic and agent modes."""
        prompt_spec = get_prompt("rag_judge")
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", prompt_spec["system"]),
                ("human", prompt_spec["user_template"]),
            ]
        )

        if self._mode == "agent":
            agent_spec = get_prompt("rag_judge_agent")
            self._agent_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", agent_spec["system"]),
                    ("placeholder", "{agent_scratchpad}"),
                    ("human", "{input}"),
                ]
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_answer(
        self,
        question: str,
        retrieved_docs: List[Document],
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """Generate a JSON answer for *question* using *retrieved_docs* as context.

        Classic mode: pre-retrieved chunks are passed directly to the LLM.
        """
        context = self._format_context(retrieved_docs)

        for attempt in range(max_retries + 1):
            try:
                messages = self.prompt.format_messages(
                    context=context, question=question
                )
                response = self.llm.invoke(messages)
                self._track_usage(question, response)

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

        raise RuntimeError("generate_answer: all retries exhausted")  # pragma: no cover

    def generate_answer_with_agent(
        self,
        question: str,
        vectorstore: Any,
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """Generate a JSON answer using the agent with FAISS search tool.

        The agent decides what to search and how many times before answering.

        Parameters
        ----------
        question : str
            The user query.
        vectorstore : FAISS
            The merged vectorstore (target + frozen competitors).
        max_retries : int
            Number of retries on JSON parse / schema errors.
        """
        from langchain.agents import AgentExecutor, create_tool_calling_agent

        from src.rag.search_tool import create_search_tool

        top_k = self._config.get("retrieval", {}).get("top_k", 5)
        search_tool = create_search_tool(vectorstore, top_k=top_k)

        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=[search_tool],
            prompt=self._agent_prompt,
        )
        executor = AgentExecutor(
            agent=agent,
            tools=[search_tool],
            max_iterations=5,
            verbose=True,
        )

        for attempt in range(max_retries + 1):
            try:
                result = executor.invoke({"input": question})
                output_text = result["output"]

                # Try to extract JSON from the output
                parsed = self._extract_json(output_text)
                self._validate_schema(parsed)

                # Track usage (agent executor doesn't expose token counts easily)
                self.token_usage.append(
                    {"question": question[:80], "usage": {"mode": "agent"}}
                )

                return parsed

            except json.JSONDecodeError as exc:
                logger.warning(
                    "Agent JSON parse error (attempt %d/%d): %s",
                    attempt + 1,
                    max_retries + 1,
                    exc,
                )
                if attempt == max_retries:
                    raise

            except ValueError as exc:
                logger.warning(
                    "Agent schema validation error (attempt %d/%d): %s",
                    attempt + 1,
                    max_retries + 1,
                    exc,
                )
                if attempt == max_retries:
                    raise

        raise RuntimeError("generate_answer_with_agent: all retries exhausted")  # pragma: no cover

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
                header += f"\n### Título: {title}"
            header += f"\n\n{doc.page_content}"
            sections.append(header)

        return "\n\n---\n\n".join(sections)

    # ------------------------------------------------------------------
    # JSON extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract JSON from agent output, handling markdown code blocks."""
        text = text.strip()

        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from ```json ... ``` blocks
        import re

        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            return json.loads(match.group(1).strip())

        # Try finding first { ... last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])

        raise json.JSONDecodeError("No JSON found in agent output", text, 0)

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
    # Token tracking
    # ------------------------------------------------------------------

    def _track_usage(self, question: str, response: Any) -> None:
        """Track token usage from a LangChain response."""
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

    def get_token_usage_summary(self) -> Dict[str, Any]:
        """Return aggregated token usage across all calls."""
        if not self.token_usage:
            return {"total_calls": 0}

        total_prompt = sum(
            u["usage"].get("prompt_tokens", 0)
            for u in self.token_usage
            if isinstance(u["usage"], dict) and "prompt_tokens" in u["usage"]
        )
        total_completion = sum(
            u["usage"].get("completion_tokens", 0)
            for u in self.token_usage
            if isinstance(u["usage"], dict) and "completion_tokens" in u["usage"]
        )

        return {
            "total_calls": len(self.token_usage),
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_prompt + total_completion,
        }
