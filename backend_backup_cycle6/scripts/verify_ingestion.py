import sys, os, asyncio
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.rag.retrieval import get_chroma_collection, get_bm25_index, get_cross_encoder, retrieve_context
from backend.rag.embeddings import encode_text_async, get_embedding_model

async def verify():
    # Preload global models
    get_embedding_model()
    get_cross_encoder()
    bm25, all_chunks = get_bm25_index()

    collection = get_chroma_collection()
    
    docs = collection.get(include=["metadatas"])
    metadatas = docs.get("metadatas", [])
    
    file_chunks = {}
    for m in metadatas:
        fname = m.get("filename", "Unknown")
        file_chunks[fname] = file_chunks.get(fname, 0) + 1
        
    print("\n" + "="*40)
    print("--- INGESTION EVIDENCE ---")
    print(f"1. Total documents in ChromaDB: {len(file_chunks)}")
    print(f"2. Total chunks in ChromaDB: {len(metadatas)}")
    print("3 & 4. Chunk count per file:")
    for fname, count in file_chunks.items():
        print(f"   {fname} = {count} chunks")
    print("="*40 + "\n")
        
    queries = [
        "Who is Dr. Supreet Khare?",
        "What awards has Dr. Khare received?",
        "What publications has Dr. Khare authored?"
    ]
    
    print("--- MANUAL RETRIEVAL VERIFICATION ---")
    for q in queries:
        print(f"\nQuestion: {q}")
        
        # Vector Search Raw
        emb = await encode_text_async(q)
        v_results = collection.query(query_embeddings=[emb], n_results=5)
        print("* Vector results (Top 5):")
        for i, m in enumerate(v_results["metadatas"][0]):
            print(f"  {i+1}. {m['filename']}")
            
        # BM25 Search Raw
        tokenized = q.lower().split()
        bm25_scores = bm25.get_scores(tokenized)
        top_n = np.argsort(bm25_scores)[::-1][:5]
        print("* BM25 results (Top 5):")
        for i, idx in enumerate(top_n):
            chunk = all_chunks[idx]
            fname = chunk.get("filename", "Unknown") if isinstance(chunk, dict) else getattr(chunk, "filename", "Unknown")
            print(f"  {i+1}. {fname}")
            
        # Pipeline execution (Hybrid RRF -> Reranking -> Source Priority Final Context)
        retrieval = await retrieve_context(q)
        print("* Reranked & Final Context (Top matches injected into Prompt):")
        for i, m in enumerate(retrieval.matches):
            print(f"  {i+1}. [{m.document}] {m.chunk[:60].replace(chr(10), ' ')}...")
            
if __name__ == "__main__":
    asyncio.run(verify())
