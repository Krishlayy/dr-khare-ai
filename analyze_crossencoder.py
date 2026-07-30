import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.rag.retrieval import search_chunks_multi, get_cross_encoder, get_chroma_collection
from rank_bm25 import BM25Okapi

async def analyze():
    queries = [
        "What is Dr. Khare's full name?",
        "What is his role at Signify Health?",
        "Where did he complete his residency?",
        "What certifications does he hold?",
        "Who is Dr. Khare?"
    ]
    
    collection = get_chroma_collection()
    total_docs = collection.count()
    print(f"Total documents in database: {total_docs}")
    
    cross_encoder = get_cross_encoder()
    
    for q in queries:
        print(f"\nQuery: {q}")
        
        # We will duplicate the logic of search_chunks_multi up to the CrossEncoder part
        # to see how many candidates are passed.
        start = time.perf_counter()
        
        from backend.rag.retrieval import _expand_query, classify_query, get_bm25_index
        from backend.rag.embeddings import encode_text_async
        variants = _expand_query(q)
        query_vectors = await asyncio.gather(*[encode_text_async(v) for v in variants])
        
        loop = asyncio.get_running_loop()
        
        def _do_vector():
            return collection.query(
                query_embeddings=query_vectors,
                n_results=min(20, collection.count()),
                include=["documents", "metadatas", "distances"],
            )
        vector_results = await loop.run_in_executor(None, _do_vector)
        
        bm25, corpus = get_bm25_index()
        all_chunks = {}
        for idx in range(len(variants)):
            v = variants[idx]
            
            # BM25 Phase
            bm25_scores = bm25.get_scores(v.split())
            bm25_candidates = 0
            for score_idx, score in enumerate(bm25_scores):
                if score > 0:
                    bm25_candidates += 1
                    raw_chunk = corpus[score_idx]["chunk"]
                    all_chunks[raw_chunk] = True

            # Vector Phase
            docs = vector_results.get("documents", [[]])[idx]
            for text in docs:
                chunk = (text or "").strip()
                if chunk:
                    all_chunks[chunk] = True
                    
            print(f"  Variant: '{v}' -> BM25 hits > 0: {bm25_candidates}")

        num_candidates = len(all_chunks)
        print(f"  Total unique candidates passed to CrossEncoder: {num_candidates}")
        
        # Time CrossEncoder on ALL candidates
        pairs = [[q, c] for c in all_chunks.keys()]
        t0 = time.perf_counter()
        scores_all = cross_encoder.predict(pairs).tolist()
        t1 = time.perf_counter()
        print(f"  CrossEncoder latency (All {num_candidates} chunks): {(t1-t0)*1000:.1f} ms")
        
        # Determine the top score from ALL candidates
        best_score_all = max(scores_all) if scores_all else 0
        best_chunk_all = list(all_chunks.keys())[scores_all.index(best_score_all)] if scores_all else "None"
        
        # Simulate Top-20 BM25 Truncation
        # Instead of score > 0, we take top 20 BM25 scores
        top20_chunks = {}
        for idx in range(len(variants)):
            v = variants[idx]
            bm25_scores = bm25.get_scores(v.split())
            
            # Get top 20 indices
            top20_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:20]
            for score_idx in top20_indices:
                if bm25_scores[score_idx] > 0:
                    raw_chunk = corpus[score_idx]["chunk"]
                    top20_chunks[raw_chunk] = True
                    
            docs = vector_results.get("documents", [[]])[idx]
            for text in docs:
                chunk = (text or "").strip()
                if chunk:
                    top20_chunks[chunk] = True

        num_top20 = len(top20_chunks)
        print(f"  Total unique candidates with Top-20 truncation: {num_top20}")
        
        pairs_top20 = [[q, c] for c in top20_chunks.keys()]
        t0 = time.perf_counter()
        scores_top20 = cross_encoder.predict(pairs_top20).tolist()
        t1 = time.perf_counter()
        print(f"  CrossEncoder latency (Top {num_top20} chunks): {(t1-t0)*1000:.1f} ms")
        
        best_score_top20 = max(scores_top20) if scores_top20 else 0
        best_chunk_top20 = list(top20_chunks.keys())[scores_top20.index(best_score_top20)] if scores_top20 else "None"
        
        print(f"  Best Score (All): {best_score_all:.4f}")
        print(f"  Best Score (Top 20): {best_score_top20:.4f}")
        
        if best_score_all == best_score_top20:
            print("  -> Quality Match: YES (Top-20 found the absolute best chunk)")
        else:
            print("  -> Quality Match: NO (Top-20 missed the best chunk)")

if __name__ == "__main__":
    asyncio.run(analyze())
