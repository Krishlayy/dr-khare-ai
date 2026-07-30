import chromadb
from backend.core.config import settings

def main():
    client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
    collection = client.get_collection(name="dr_khare_docs")
    
    # Get all chunks
    results = collection.get(
        where={"source": "complete_verified_profile.txt"}
    )
    
    documents = results['documents']
    count = len(documents)
    
    sizes = [len(doc) for doc in documents]
    avg_size = sum(sizes) / count if count > 0 else 0
    max_size = max(sizes) if count > 0 else 0
    
    print(f"Chunk Count: {count}")
    print(f"Average Chunk Size: {avg_size:.2f} characters")
    print(f"Largest Chunk Size: {max_size} characters\n")
    
    queries = ["Education", "Employment", "Publications", "Awards"]
    
    for q in queries:
        print(f"=== Top 10 Retrieved Chunks for: {q} ===")
        res = collection.query(
            query_texts=[q],
            n_results=10,
            where={"source": "complete_verified_profile.txt"}
        )
        for i, (doc, meta, dist) in enumerate(zip(res['documents'][0], res['metadatas'][0], res['distances'][0])):
            preview = doc.replace('\n', ' ')[:150] + "..."
            print(f"[{i+1}] Score: {dist:.4f} | Chunk ID: {meta.get('chunk_index', 'N/A')} | Preview: {preview}")
        print("\n")

if __name__ == "__main__":
    main()
