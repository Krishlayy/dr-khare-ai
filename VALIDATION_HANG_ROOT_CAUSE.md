# Root Cause Analysis: Validation Script Hang

## 1. Issue Description
The `run_validation.py` script hung indefinitely on Question 1 (`[1/500] Q: What is Dr. Khare's full name?`) for over 34 minutes without crashing or moving to the next question.

## 2. Root Cause
The hang occurred during the LLM generation phase inside `backend.services.llm_service.py`. The script successfully loaded all retrieval models (BM25 and `ms-marco` cross-encoder) and completed the context retrieval step, but froze when executing the external HTTP POST request to the LLM provider (Groq/Ollama).

While `httpx.AsyncClient` was configured with a default `timeout=300.0` in `http_client.py`, HTTP client timeouts can sometimes fail to trigger if a TCP connection is kept alive but no data is transmitted, or if the server introduces extreme artificial delays (such as rate-limiting deadlocks). Because the validation script processed questions in a blocking `await` without an event loop-level timeout, the entire benchmark halted permanently.

## 3. Remediation Plan

**1. Strict Event Loop Timeouts:**
Wrap all external LLM calls (`_generate_groq` and `_generate_ollama`) with `asyncio.wait_for(..., timeout=20.0)`. This guarantees the event loop will forcefully terminate the awaitable if the API hangs, throwing a `TimeoutError`.

**2. Fault Tolerance:**
Ensure `run_validation.py` explicitly catches `TimeoutError` and logs it as a failed question rather than crashing.

**3. Incremental Saving:**
Change the file writing strategy in `run_validation.py`. Instead of aggregating all 500 results in memory and writing at the end, the script will:
- Open `benchmark_results.csv` in append (`"a"`) mode.
- Write each result to disk immediately after the question finishes.
- Do the same for `failures.md`.

**4. Per-Question Logging:**
Add clear console logging with elapsed time for every question to ensure visibility into the pipeline's progress.
