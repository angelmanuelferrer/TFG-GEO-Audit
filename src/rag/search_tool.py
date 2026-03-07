"""FAISS search tool for the RAG Judge agent.

Wraps FAISS retrieval as a LangChain @tool so the agent LLM can
invoke it like a web search engine. The agent decides what query to
send (original or reformulated) and receives formatted chunks back.
See ADR-012 in docs/DECISIONS.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.tools import tool

if TYPE_CHECKING:
    from langchain_community.vectorstores import FAISS


def create_search_tool(vectorstore: "FAISS", top_k: int = 5):
    """Return a LangChain tool that searches the given FAISS vectorstore.

    Parameters
    ----------
    vectorstore : FAISS
        The merged vectorstore (target + frozen competitors).
    top_k : int
        Number of chunks to return per search.
    """
    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})

    @tool
    def search(query: str) -> str:
        """Busca en el indice de paginas web. Devuelve fragmentos relevantes con sus URLs y titulos."""
        docs = retriever.invoke(query)

        if not docs:
            return "No se encontraron resultados relevantes."

        sections = []
        for i, doc in enumerate(docs, 1):
            url = doc.metadata.get("source_url", "Desconocida")
            title = doc.metadata.get("title", "")
            header = f"[Resultado {i}] {url}"
            if title:
                header += f"\nTitulo: {title}"
            header += f"\n\n{doc.page_content}"
            sections.append(header)

        return "\n\n---\n\n".join(sections)

    return search
