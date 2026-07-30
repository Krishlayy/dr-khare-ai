import os
import re
import glob
from pathlib import Path
import chromadb
from backend.core.config import settings
from backend.rag.document_processor import extract_text, clean_text, chunk_text

COLLECTION_NAME = "dr_khare_docs"
UPLOAD_DIR = Path(settings.UPLOAD_DIR)

def main():
    print("=" * 60)
    print("REINDEX \u2014 Dr. Khare Clean Corpus")
    print("=" * 60)
    print()

    client = chromadb.PersistentClient(path=settings.CHROMA_PATH)

    print("[1/4] Wiping existing ChromaDB collection...")
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"     Deleted collection: {COLLECTION_NAME}")
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )
    print(f"     Created fresh collection: {COLLECTION_NAME}")
    print()

    print("[2/4] Indexing all clean corpus text files...")
    
    approved_files = glob.glob(str(UPLOAD_DIR / "*.txt")) + glob.glob(str(UPLOAD_DIR / "*.md"))
    
    total_chunks = 0
    all_chunks = []

    for path in approved_files:
        path_obj = Path(path)
        print(f"     Processing: {path_obj.name}")

        raw_text = extract_text(str(path_obj))
        cleaned = clean_text(raw_text)
        chunks = chunk_text(cleaned, chunk_size=800, overlap=120)

        for i, chunk in enumerate(chunks):
            doc_id = f"{path_obj.stem}_chunk_{i}"
            all_chunks.append({
                "id": doc_id,
                "text": chunk,
                "metadata": {"source": path_obj.name, "filename": path_obj.name, "chunk_index": i}
            })
            total_chunks += 1

        print(f"     Indexed {len(chunks)} chunks from {path_obj.name}")

    print("\n[3/4] Inserting chunks into ChromaDB...")
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        collection.add(
            documents=[b["text"] for b in batch],
            metadatas=[b["metadata"] for b in batch],
            ids=[b["id"] for b in batch]
        )
    print(f"\n     Total in collection: {collection.count()} chunks\n")

    print("[4/4] Verifying retrieval...")
    test_queries = [
        "Where did Dr. Khare do his residency?",
        "What is Dr. Khare's current role?",
        "Where did Dr. Khare work before moving to the USA?"
    ]

    for query in test_queries:
        try:
            results = collection.query(
                query_texts=[query],
                n_results=1
            )
            doc = results['metadatas'][0][0]['source'] if results['metadatas'] and results['metadatas'][0] else 'None'
            score = results['distances'][0][0] if results['distances'] and results['distances'][0] else 0.0
            min_score = settings.SIMILARITY_THRESHOLD
            
            status = "PASS" if score <= min_score else "FAIL"
            print(f"     [{status}] '{query[:40]}' -> score={score:.4f} doc={doc}")
        except Exception as e:
            print(f"     Error querying '{query[:40]}': {e}")
            
    print("\n[4/4] Reindexing complete.")
    print("=" * 60)

if __name__ == "__main__":
    main()
