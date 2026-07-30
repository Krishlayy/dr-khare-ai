# REINDEX REPORT — Dr. Khare Knowledge Base
_Generated: 2026-06-07 03:53:55_

## Summary
- Total chunks in ChromaDB: **219**
- Biography summary chunk: **1** (injected manually)
- Document chunks: **218**
- Duplicate chunks: **1**

## Documents Indexed

| Filename | Chunks | Path |
|----------|--------|------|
| Biography Summary (injected) | 1 | N/A — hand-crafted |
| MASTER CV.pdf | 216 | C:\Users\hello\dr_khare_ai\storage\uploads\8142248431b7_MASTER CV.pdf |
| clinic_info.txt | 2 | C:\Users\hello\dr_khare_ai\storage\uploads\clinic_info.txt |

## Retrieval Verification

| Query | Score | Doc | Status |
|-------|-------|-----|--------|
| who is dr khare | 0.5775 | clinic_info.txt | ✅ PASS |
| Dr Supreet Khare biography background | 0.4829 | clinic_info.txt | ✅ PASS |
| what are dr khare qualifications | 0.5857 | clinic_info.txt | ✅ PASS |
| dr khare specialty | 0.6610 | clinic_info.txt | ✅ PASS |
| where did dr khare study | 0.5474 | clinic_info.txt | ✅ PASS |

## Configuration
- WEB_FALLBACK_THRESHOLD: 0.35 (identity queries bypass threshold entirely)
- SIMILARITY_THRESHOLD: 0.35
- TOP_K_CHUNKS: 5

## SPECIAL_QUERIES (bypass threshold, force KB retrieval)

- Who is Dr Supreet Khare?
- Tell me about Dr Khare
- Dr Khare biography and background
- What is Dr Khare professional profile?
- Summarize Dr Khare qualifications
- Dr Khare education and training
- What does Dr Khare do?
- Dr Khare physician profile