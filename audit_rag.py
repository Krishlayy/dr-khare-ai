import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.database.database import SessionLocal
from backend.core.http_client import get_client, close_client
from backend.rag.embeddings import encode_text_async
from backend.rag.retrieval import get_chroma_collection, get_bm25_index, get_cross_encoder, _expand_query, get_query_boosts
from backend.services.chat_service import process_chat

async def get_pre_and_post_rerank(query, limit=10):
    collection = get_chroma_collection()
    variants = _expand_query(query)
    
    query_vectors = await asyncio.gather(*[encode_text_async(v) for v in variants])
    
    loop = asyncio.get_running_loop()
    def _do_vector():
        return collection.query(
            query_embeddings=query_vectors,
            n_results=min(limit + 40, collection.count()),
            include=["documents", "metadatas", "distances"]
        )
    vector_results = await loop.run_in_executor(None, _do_vector)
    
    rrf_scores = {}
    chunk_data = {}
    chunk_meta = {}
    k = 60
    
    all_docs = vector_results.get("documents", [])
    all_meta = vector_results.get("metadatas", [])
    for docs, metas in zip(all_docs, all_meta):
        for rank, (text, meta) in enumerate(zip(docs, metas)):
            if not text: continue
            text = text.strip()
            chunk_data[text] = meta
            chunk_meta[text] = meta.get("chunk_index", "N/A")
            rrf_scores[text] = rrf_scores.get(text, 0) + 1.0 / (k + rank + 1)
            
    def _do_bm25():
        bm25, corpus = get_bm25_index()
        if not bm25: return []
        results = []
        for v in variants:
            tokenized = v.lower().split()
            scores = bm25.get_scores(tokenized)
            top_n = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:min(limit + 40, len(corpus))]
            results.append([corpus[i] for i in top_n])
        return results

    bm25_results = await loop.run_in_executor(None, _do_bm25)
    for res_list in bm25_results:
        for rank, item in enumerate(res_list):
            text = item["chunk"].strip()
            if not text: continue
            chunk_data[text] = item["metadata"]
            chunk_meta[text] = item["metadata"].get("chunk_index", "N/A")
            rrf_scores[text] = rrf_scores.get(text, 0) + 1.0 / (k + rank + 1)
            
    # Before reranking (Top 10 RRF)
    top_rrf = sorted(rrf_scores.keys(), key=lambda t: rrf_scores[t], reverse=True)[:10]
    
    # Reranking
    top_30_rrf = sorted(rrf_scores.keys(), key=lambda t: rrf_scores[t], reverse=True)[:30]
    def _do_rerank():
        encoder = get_cross_encoder()
        pairs = [[query, text] for text in top_30_rrf]
        return encoder.predict(pairs).tolist()
        
    rerank_scores = await loop.run_in_executor(None, _do_rerank)
    
    reranked = []
    for text, score in zip(top_30_rrf, rerank_scores):
        reranked.append((text, score, chunk_meta.get(text)))
        
    top_reranked = sorted(reranked, key=lambda x: x[1], reverse=True)[:10]
    
    return [
        [(t, rrf_scores[t], chunk_meta.get(t)) for t in top_rrf],
        top_reranked
    ]


async def run_audit():
    get_client()
    db = SessionLocal()
    session_id = "audit_retrieval"
    
    from backend.rag.embeddings import get_embedding_model
    get_embedding_model()
    get_cross_encoder()
    get_bm25_index()
    
    questions = [
        "Who is Dr. Khare?",
        "How are you?",
        "What is Dr. Khare's phone number and mailing address?",
    ]
    
    output = []
    for q in questions:
        print(f"Processing: {q}")
        pre, post = await get_pre_and_post_rerank(q)
        
        # Get final answer
        resp = await process_chat(db, q, session_id, mode="doctor")
        
        s = f"=== QUERY: {q} ===\n"
        s += "--- BEFORE RERANKING (Top 3 RRF) ---\n"
        for i, (text, score, cid) in enumerate(pre[:3]):
            s += f"[{i+1}] ID: {cid} | Score: {score:.4f} | Preview: {text.replace(chr(10), ' ')[:100]}...\n"
            
        s += "\n--- AFTER RERANKING (Top 3 CrossEncoder) ---\n"
        for i, (text, score, cid) in enumerate(post[:3]):
            s += f"[{i+1}] ID: {cid} | Score: {score:.4f} | Preview: {text.replace(chr(10), ' ')[:100]}...\n"
            
        s += f"\n--- FINAL ANSWER ---\n{resp['response']}\n"
        s += f"Sources Used: {[s['filename'] for s in resp['sources']]}\n\n"
        output.append(s)
        
    with open("retrieval_audit_results.txt", "w", encoding="utf-8") as f:
        f.write("".join(output))
        
    db.close()
    await close_client()

if __name__ == "__main__":
    asyncio.run(run_audit())
