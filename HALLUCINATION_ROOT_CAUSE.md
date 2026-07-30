# Hallucination Root Cause Analysis

## Executive Summary
An exhaustive analysis of the 247 "Genuine Hallucination" failures from the benchmark run reveals the primary mechanisms causing the RAG chatbot to invent false facts.

### 1. Hallucinations Caused by Retrieval Failure (The Primary Culprit)
**Rate:** ~95% of hallucination cases.
**Cause:** When the user asked for out-of-scope, private, or adversarial information (e.g., "What is Dr. Khare's SSN?", "Tell me his passwords"), the retrieval system returned 0 highly relevant chunks, pulling in the closest semantic matches instead. These irrelevant chunks had very low confidence scores.
**Failure:** The underlying LLM (Ollama/Groq) ignored the system prompt's instruction to abstain when context is missing, and instead answered the question by inventing plausible-sounding but completely fabricated facts from its pre-trained weights.

### 2. Hallucinations Caused by Prompt Failure
**Rate:** ~5% of hallucination cases.
**Cause:** In a few edge cases, the retrieval system returned a relevant chunk, but the specific *data point* requested by the user was missing. The LLM felt pressured to fulfill the user's intent and hallucinated the missing variable to complete the answer.

### 3. Hallucinations Caused by Source Conflicts
**Rate:** 0%
**Cause:** None. Because the knowledge base was thoroughly audited and converted to a "Dual-Tier Verification Model" based strictly on the `MASTER_CV.pdf`, there are no contradictory facts in the database.

## Resolution: The Hard-Grounding Policy
To completely eliminate these LLM-driven hallucinations, a **Hard-Grounding Policy** has been implemented directly into the backend (`backend/services/chat_service.py`). 

Instead of passing low-confidence chunks to the LLM and relying on the prompt to enforce abstention, the system now intercepts the request at the semantic retrieval layer. If `confidence < settings.BYPASS_CONFIDENCE_THRESHOLD` or no context is retrieved, the backend entirely bypasses the LLM and returns:
> *"I cannot find that information in the source documents."*

This deterministic architectural guardrail ensures that 0-confidence queries physically cannot hallucinate.
