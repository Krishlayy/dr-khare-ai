import sys, os, asyncio, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.rag.retrieval import get_chroma_collection
from backend.rag.embeddings import get_embedding_model

def audit_chroma():
    collection = get_chroma_collection()
    count = collection.count()
    
    docs = collection.get(include=["documents", "metadatas", "embeddings"])
    
    unique_chunks = set()
    unique_embeddings = set()
    
    for d, e in zip(docs["documents"], docs["embeddings"]):
        unique_chunks.add(d)
        unique_embeddings.add(tuple(e))
        
    print(f"\n--- CHROMADB AUDIT ---")
    print(f"Collection Size: {count}")
    print(f"Embedding Dimension: {len(docs['embeddings'][0]) if docs['embeddings'] is not None and len(docs['embeddings']) > 0 else 0}")
    print(f"Total Unique Chunks: {len(unique_chunks)}")
    print(f"Total Unique Embeddings: {len(unique_embeddings)}")
    
    duplicates = count - len(unique_chunks)
    print(f"Duplicate Chunks Detected: {duplicates}")

if __name__ == "__main__":
    audit_chroma()
