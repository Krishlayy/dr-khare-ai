import os
import re
import subprocess
import time

def replace_in_file(filepath, pattern, replacement):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(pattern, replacement, content)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def update_chunking(size, overlap):
    # Update document_processor.py
    dp_path = r"backend\rag\document_processor.py"
    replace_in_file(dp_path, r'CHUNK_SIZE\s*=\s*\d+', f'CHUNK_SIZE = {size}')
    replace_in_file(dp_path, r'CHUNK_OVERLAP\s*=\s*\d+', f'CHUNK_OVERLAP = {overlap}')
    replace_in_file(dp_path, r'chunk_size:\s*int\s*=\s*\d+', f'chunk_size: int = {size}')
    replace_in_file(dp_path, r'overlap:\s*int\s*=\s*\d+', f'overlap: int = {overlap}')
    
    # Update reindex_approved.py
    reindex_path = r"reindex_approved.py"
    replace_in_file(reindex_path, r'chunk_size=\d+', f'chunk_size={size}')
    replace_in_file(reindex_path, r'overlap=\d+', f'overlap={overlap}')

def run_reindex():
    subprocess.run(["python", "reindex_approved.py"], capture_output=True)

def update_candidates(pool_size, ce_size):
    retrieval_path = r"backend\rag\retrieval.py"
    replace_in_file(retrieval_path, r'limit=min\(limit \*\s*\d+', f'limit=min(limit * {pool_size//5}')
    # Note: the code in retrieval.py might look different. Let's inspect it first!
    pass

def run_eval():
    result = subprocess.run(["python", "backend/scripts/eval_retrieval.py"], capture_output=True, text=True)
    out = result.stdout
    try:
        r1 = re.search(r'Recall@1:\s*([\d\.]+)', out).group(1)
        r3 = re.search(r'Recall@3:\s*([\d\.]+)', out).group(1)
        r5 = re.search(r'Recall@5:\s*([\d\.]+)', out).group(1)
        mrr = re.search(r'MRR:\s*([\d\.]+)', out).group(1)
        return float(r1), float(r3), float(r5), float(mrr)
    except:
        return 0,0,0,0

if __name__ == "__main__":
    print("Running Grid Search...")
    with open("grid_search_results.csv", "w") as f:
        f.write("ChunkSize,Overlap,Recall1,Recall3,Recall5,MRR\n")
        
        for size in [700, 800, 900]:
            for overlap in [100, 150, 200, 250]:
                print(f"Testing {size} / {overlap}...")
                update_chunking(size, overlap)
                run_reindex()
                r1, r3, r5, mrr = run_eval()
                print(f"Result: R@3={r3}")
                f.write(f"{size},{overlap},{r1},{r3},{r5},{mrr}\n")
                f.flush()
    print("Done!")
