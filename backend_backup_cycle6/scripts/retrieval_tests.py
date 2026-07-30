"""Verify RAG retrieval for production test queries."""
from backend.rag.retrieval import retrieve_context, search_chunks

TEST_QUERIES = [
    "Who is Dr Khare?",
    "What are Dr Khare office hours?",
    "What education does Dr Khare have?",
]


def main() -> None:
    print("=" * 60)
    print("RAG RETRIEVAL VERIFICATION")
    print("=" * 60)

    for query in TEST_QUERIES:
        print(f"\nQuery: {query}")
        print("-" * 40)
        matches = search_chunks(query, limit=5)
        result = retrieve_context(query)

        for i, m in enumerate(matches, 1):
            print(f"  [{i}] score={m.score:.4f} doc={m.document}")
            print(f"      chunk: {m.chunk[:120]}...")

        print(f"  Context built: {'YES' if result.context else 'NO'}")
        print(f"  Confidence: {result.confidence:.4f}")
        print(f"  Web fallback: {result.use_web_fallback}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
