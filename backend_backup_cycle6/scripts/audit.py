import json
import glob
import os

def audit():
    print("=== CORPUS AUDIT ===")
    
    # 1. Inventory
    files = glob.glob('storage/uploads/*')
    for f in files:
        size = os.path.getsize(f)
        print(f"File: {os.path.basename(f)} | Size: {size} bytes")
        
    # 2. Retrieval Frequency
    try:
        with open('eval_results_v2.json', 'r') as f:
            data = json.load(f)
            
        retrieval_counts = {}
        expected_counts = {}
        
        for q in data.get('results', []):
            retrieved = q.get('sources', [])
            for doc in retrieved:
                retrieval_counts[doc] = retrieval_counts.get(doc, 0) + 1
                
        print("\n=== EXPECTED CITATION FREQUENCY ===")
        for doc, count in sorted(expected_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"{doc}: {count}")
            
        print("\n=== ACTUAL RETRIEVAL FREQUENCY (Top 5) ===")
        for doc, count in sorted(retrieval_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"{doc}: {count}")
            
    except Exception as e:
        print("Could not load eval_results_v2.json:", e)

if __name__ == '__main__':
    audit()
