"""Utility script to verify ChromaDB semantic search."""
from backend.rag.retrieval import get_strict_context

if __name__ == "__main__":
    query = "What are the office hours?"
    context, sources = get_strict_context(query)
    if not context:
        print("No results found. Upload documents via /api/upload first.")
    else:
        print(f"--- Search Result for: {query} ---")
        print(context[:500])
        print("Sources:", sources)
