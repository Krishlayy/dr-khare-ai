with open("backend/services/chat_service.py", "r", encoding="utf-8") as f:
    code = f.read()

verify_func = """
async def verify_grounding(answer: str, context: str, model: str) -> bool:
    prompt = f\"\"\"
Given the context and the answer, verify if the answer is ENTIRELY supported by the context.
If any factual claim in the answer is NOT explicitly present in the context, output VERIFICATION_FAILED.
If the answer is fully supported by the context, output VERIFIED.
Only output VERIFICATION_FAILED or VERIFIED.

CONTEXT:
{context}

ANSWER:
{answer}

OUTPUT:\"\"\"
    from backend.services.llm_service import generate_response
    verification = await generate_response(prompt, model=model)
    return "VERIFICATION_FAILED" not in verification.upper()
"""

code = code.replace("async def process_chat(", verify_func + "\nasync def process_chat(")

old_call = """    model = await get_selected_model()
    answer = await generate_response(prompt, model=model)
    elapsed = int((time.perf_counter() - start) * 1000)"""

new_call = """    model = await get_selected_model()
    answer = await generate_response(prompt, model=model)
    
    if mode == MODE_DOCTOR and has_context and confidence >= settings.SIMILARITY_THRESHOLD:
        is_verified = await verify_grounding(answer, context, model)
        if not is_verified:
            logger.info("Hard Grounding Verification Failed! Answer: %s", answer)
            answer = "That information is not available in the source documents."
            
    elapsed = int((time.perf_counter() - start) * 1000)"""

code = code.replace(old_call, new_call)

with open("backend/services/chat_service.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Modified chat_service.py")
