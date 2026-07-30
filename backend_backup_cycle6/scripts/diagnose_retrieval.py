from backend.rag.retrieval import debug_search, retrieve_context

queries = [
    "Who is Dr Khare?",
    "What are Dr Khare office hours?",
    "What education does Dr Khare have?",
]

for q in queries:
    matches = debug_search(q, limit=5)
    result = retrieve_context(q)
    print("===", q)
    print("debug matches:", len(matches))
    for m in matches[:3]:
        print("  score=", m["score"], "doc=", m["document"])
        print("  chunk=", (m["chunk"] or "")[:100])
    print("context:", "YES" if result.context else "NO", "sources:", len(result.sources))
    print("confidence:", result.confidence, "web_fallback:", result.use_web_fallback)
    print()
