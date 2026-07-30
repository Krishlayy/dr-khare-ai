import sys, os, asyncio, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.rag.retrieval import get_chroma_collection, get_bm25_index, get_cross_encoder, _expand_query
from backend.rag.embeddings import encode_text_async, get_embedding_model
from backend.services.llm_service import generate_response

async def profile_query(query: str):
    # PRELOAD (Exclude from query latency)
    get_embedding_model()
    get_cross_encoder()
    get_bm25_index()
    
    limit = 3
    collection = get_chroma_collection()
    
    print(f"\n--- PROFILING: {query} ---")
    start_total = time.perf_counter()
    
    # 1. Query Preprocessing
    t0 = time.perf_counter()
    variants = _expand_query(query)
    query_vectors = await asyncio.gather(*[encode_text_async(v) for v in variants])
    t_preprocessing = (time.perf_counter() - t0) * 1000
    
    # 2. Vector Retrieval
    t0 = time.perf_counter()
    loop = asyncio.get_running_loop()
    def _do_vector():
        return collection.query(
            query_embeddings=query_vectors,
            n_results=min(limit + 10, collection.count()),
            include=["documents", "metadatas", "distances"]
        )
    vector_results = await loop.run_in_executor(None, _do_vector)
    t_vector = (time.perf_counter() - t0) * 1000
    
    # 3. BM25 Retrieval
    t0 = time.perf_counter()
    def _do_bm25():
        bm25, corpus = get_bm25_index()
        results = []
        for v in variants:
            tokenized = v.lower().split()
            scores = bm25.get_scores(tokenized)
            top_n = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:min(limit + 10, len(corpus))]
            results.append([corpus[i] for i in top_n])
        return results
    bm25_results = await loop.run_in_executor(None, _do_bm25)
    t_bm25 = (time.perf_counter() - t0) * 1000
    
    # 4. RRF Fusion
    t0 = time.perf_counter()
    rrf_scores = {}
    chunk_data = {}
    k = 60
    
    all_docs = vector_results.get("documents", [])
    all_meta = vector_results.get("metadatas", [])
    for docs, metas in zip(all_docs, all_meta):
        for rank, (text, meta) in enumerate(zip(docs, metas)):
            if not text: continue
            text = text.strip()
            chunk_data[text] = meta
            rrf_scores[text] = rrf_scores.get(text, 0) + 1.0 / (k + rank + 1)
            
    for res_list in bm25_results:
        for rank, item in enumerate(res_list):
            text = item["chunk"].strip()
            if not text: continue
            chunk_data[text] = item["metadata"]
            rrf_scores[text] = rrf_scores.get(text, 0) + 1.0 / (k + rank + 1)
            
    top_rrf = sorted(rrf_scores.keys(), key=lambda t: rrf_scores[t], reverse=True)[:20]
    t_rrf = (time.perf_counter() - t0) * 1000
    
    # 5. CrossEncoder
    t0 = time.perf_counter()
    def _do_rerank():
        encoder = get_cross_encoder()
        pairs = [[query, text] for text in top_rrf]
        return encoder.predict(pairs).tolist()
    rerank_scores = await loop.run_in_executor(None, _do_rerank)
    t_crossencoder = (time.perf_counter() - t0) * 1000
    
    # 6. Context Assembly
    t0 = time.perf_counter()
    final_chunks = []
    import math
    for text, score in zip(top_rrf, rerank_scores):
        meta = chunk_data.get(text, {})
        filename = (meta or {}).get("filename", "Unknown")
        final_chunks.append((filename, text, score))
    merged = sorted(final_chunks, key=lambda x: x[2], reverse=True)[:limit]
    
    context = "\n\n---\n\n".join(
        f"[DOCUMENT]\nFilename: {f}\n\nCONTENT:\n{c}".strip()
        for f, c, s in merged
    )
    t_context = (time.perf_counter() - t0) * 1000
    
    # 7. Ollama Generation
    t0 = time.perf_counter()
    prompt = f"Context: {context}\nQuestion: {query}\nAnswer:"
    answer = await generate_response(prompt, temperature=0.0)
    t_ollama = (time.perf_counter() - t0) * 1000
    
    t_total = (time.perf_counter() - start_total) * 1000
    
    print("\n| Component        | Time(ms) |")
    print("| ---------------- | -------- |")
    print(f"| Preprocessing    | {t_preprocessing:8.1f} |")
    print(f"| BM25             | {t_bm25:8.1f} |")
    print(f"| Vector           | {t_vector:8.1f} |")
    print(f"| RRF Fusion       | {t_rrf:8.1f} |")
    print(f"| CrossEncoder     | {t_crossencoder:8.1f} |")
    print(f"| Context Assembly | {t_context:8.1f} |")
    print(f"| Ollama           | {t_ollama:8.1f} |")
    print(f"| Total            | {t_total:8.1f} |")

async def main():
    from backend.core.http_client import get_client, close_client
    get_client()
    await profile_query("What awards has Dr. Khare received?")
    await close_client()

if __name__ == "__main__":
    asyncio.run(main())
