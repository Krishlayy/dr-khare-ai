import sys, os, asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.rag.retrieval import get_chroma_collection, get_bm25_index, get_cross_encoder, _expand_query
from backend.rag.embeddings import encode_text_async, get_embedding_model

async def audit_query(query: str):
    get_embedding_model()
    get_cross_encoder()
    get_bm25_index()
    
    limit = 5
    collection = get_chroma_collection()
    
    print(f"\n========================================\nQuery: {query}\n========================================")
    
    variants = _expand_query(query)
    query_vectors = await asyncio.gather(*[encode_text_async(v) for v in variants])
    
    loop = asyncio.get_running_loop()
    def _do_vector():
        return collection.query(
            query_embeddings=query_vectors,
            n_results=min(15, collection.count()),
            include=["documents", "metadatas", "distances"]
        )
    vector_results = await loop.run_in_executor(None, _do_vector)
    
    def _do_bm25():
        bm25, corpus = get_bm25_index()
        results = []
        for v in variants:
            tokenized = v.lower().split()
            scores = bm25.get_scores(tokenized)
            top_n = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:min(15, len(corpus))]
            results.append([corpus[i] for i in top_n])
        return results
    bm25_results = await loop.run_in_executor(None, _do_bm25)
    
    rrf_scores = {}
    chunk_data = {}
    k = 60
    
    v_files = []
    all_docs = vector_results.get("documents", [])
    all_meta = vector_results.get("metadatas", [])
    for docs, metas in zip(all_docs, all_meta):
        for rank, (text, meta) in enumerate(zip(docs, metas)):
            if not text: continue
            text = text.strip()
            chunk_data[text] = meta
            rrf_scores[text] = rrf_scores.get(text, 0) + 1.0 / (k + rank + 1)
            v_files.append((meta or {}).get("filename", "Unknown"))
            
    b_files = []
    for res_list in bm25_results:
        for rank, item in enumerate(res_list):
            text = item["chunk"].strip()
            if not text: continue
            chunk_data[text] = item["metadata"]
            rrf_scores[text] = rrf_scores.get(text, 0) + 1.0 / (k + rank + 1)
            b_files.append(item["metadata"].get("filename", "Unknown"))
            
    top_rrf = sorted(rrf_scores.keys(), key=lambda t: rrf_scores[t], reverse=True)[:15]
    
    def _do_rerank():
        encoder = get_cross_encoder()
        pairs = [[query, text] for text in top_rrf]
        return encoder.predict(pairs).tolist()
    rerank_scores = await loop.run_in_executor(None, _do_rerank)
    
    final_chunks = []
    import math
    from backend.rag.retrieval import SOURCE_PRIORITY, get_query_boosts
    boosts = get_query_boosts(query)
    
    for text, score in zip(top_rrf, rerank_scores):
        meta = chunk_data.get(text, {})
        filename = (meta or {}).get("filename", "Unknown")
        priority = SOURCE_PRIORITY.get(filename, 0.6)
        cat_boost = boosts.get(filename, 1.0)
        
        try:
            sigmoid_score = 1 / (1 + math.exp(-score))
        except OverflowError:
            sigmoid_score = 0.0 if score < 0 else 1.0
            
        final_score = sigmoid_score * priority * cat_boost
        final_chunks.append((filename, text, final_score, sigmoid_score, priority, cat_boost))
        
    merged = sorted(final_chunks, key=lambda x: x[2], reverse=True)[:limit]
    
    print("* Vector Top Results:")
    for f in list(dict.fromkeys(v_files))[:5]: print(f"  - {f}")
    
    print("\n* BM25 Top Results:")
    for f in list(dict.fromkeys(b_files))[:5]: print(f"  - {f}")
    
    print("\n* RRF Top Candidate Files:")
    for f in list(dict.fromkeys([chunk_data.get(t, {}).get("filename", "Unknown") for t in top_rrf]))[:5]:
        print(f"  - {f}")
        
    print("\n* Final Merged Context (Top 5):")
    for f, c, s, sig, pri, bst in merged:
        print(f"  - [{f}] Score: {s:.4f} (Sigmoid:{sig:.4f} * Priority:{pri} * Boost:{bst}) -> {c[:40].replace(chr(10), ' ')}...")

async def main():
    queries = [
        "Who is Dr. Supreet Khare?",
        "What awards has Dr. Khare received?",
        "What publications has Dr. Khare authored?"
    ]
    for q in queries:
        await audit_query(q)

if __name__ == "__main__":
    asyncio.run(main())
