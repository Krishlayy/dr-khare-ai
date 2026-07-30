import re

with open("backend/rag/retrieval.py", "r", encoding="utf-8") as f:
    code = f.read()

# Add classify_query function
classification_code = """
def classify_query(query: str) -> str:
    ql = query.lower()
    
    # Priority matches
    if "acls" in ql or "bls" in ql or "certifi" in ql or "dea" in ql or "license" in ql or "course" in ql:
        return "certification"
    if "research" in ql or "icmr" in ql or "study" in ql or "project" in ql or "trial" in ql or "lab" in ql:
        return "research"
    if "member" in ql or "society" in ql or "association" in ql or "ifmsa" in ql or "acp" in ql or "ama" in ql or "role" in ql:
        return "membership"
    if "publish" in ql or "publication" in ql or "article" in ql or "journal" in ql or "paper" in ql or "author" in ql:
        return "publication"
    if "volunteer" in ql or "community" in ql or "service" in ql or "ngo" in ql or "prayas" in ql or "deep griha" in ql:
        return "volunteer"
    if "award" in ql or "honor" in ql or "prize" in ql or "recognition" in ql or "medal" in ql or "scholarship" in ql or "won" in ql or "quiz" in ql:
        return "awards"
    if "education" in ql or "degree" in ql or "college" in ql or "university" in ql or "school" in ql or "residency" in ql or "mbbs" in ql or "graduate" in ql:
        return "education"
    if "employment" in ql or "work" in ql or "position" in ql or "job" in ql or "clinic" in ql or "hospital" in ql or "director" in ql or "ceo" in ql:
        return "employment"
        
    # Biography fallback
    if "who" in ql or "background" in ql or "born" in ql or "profile" in ql or "about" in ql or "language" in ql or "speak" in ql or "hobby" in ql:
        return "biography"
        
    return None
"""

code = code.replace("def get_query_boosts", classification_code + "\ndef get_query_boosts")

# Modify search_chunks_multi to use the where filter
old_do_vector = '''    def _do_vector():
        return collection.query(
            query_embeddings=query_vectors,
            n_results=min(limit + 40, collection.count()),
            include=["documents", "metadatas", "distances"]
        )'''

new_do_vector = '''    def _do_vector():
        category = classify_query(query)
        where_filter = {"category": category} if category else None
        return collection.query(
            query_embeddings=query_vectors,
            n_results=min(limit + 40, collection.count()),
            include=["documents", "metadatas", "distances"],
            where=where_filter
        )'''

code = code.replace(old_do_vector, new_do_vector)

old_bm25 = '''    def _do_bm25():
        bm25, corpus = get_bm25_index()
        if not bm25: return []
        results = []
        for v in variants:
            tokenized = v.lower().split()
            scores = bm25.get_scores(tokenized)
            top_n = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:min(limit + 40, len(corpus))]
            results.append([corpus[i] for i in top_n])
        return results'''

new_bm25 = '''    def _do_bm25():
        bm25, corpus = get_bm25_index()
        if not bm25: return []
        category = classify_query(query)
        results = []
        for v in variants:
            tokenized = v.lower().split()
            scores = bm25.get_scores(tokenized)
            # Filter scores by category
            valid_indices = []
            for i in range(len(scores)):
                if not category or corpus[i]["metadata"].get("category") == category:
                    valid_indices.append(i)
            
            top_n = sorted(valid_indices, key=lambda i: scores[i], reverse=True)[:min(limit + 40, len(valid_indices))]
            results.append([corpus[i] for i in top_n])
        return results'''

code = code.replace(old_bm25, new_bm25)

with open("backend/rag/retrieval.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Modified retrieval.py")
