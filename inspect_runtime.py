import asyncio
from backend.core.config import settings
from backend.services.llm_service import _providers, get_selected_model, get_ollama_status, cb
from backend.database.database import SessionLocal
from backend.database.models import Analytics

async def inspect():
    print("--- RUNTIME CONFIGURATION ---")
    print(f"PRIMARY_PROVIDER: {settings.PRIMARY_PROVIDER}")
    print(f"FALLBACK_PROVIDER: {settings.FALLBACK_PROVIDER}")
    
    selected = await get_selected_model()
    print(f"Currently selected provider via get_selected_model(): {selected}")
    
    print("\n--- PROVIDER INITIALIZATION ---")
    groq_provider = _providers.get("groq")
    ollama_provider = _providers.get("ollama")
    
    groq_init = "Yes" if groq_provider else "No"
    ollama_init = "Yes" if ollama_provider else "No"
    
    print(f"GroqProvider Initialized: {groq_init}")
    print(f"OllamaProvider Initialized: {ollama_init}")
    
    if groq_provider:
        has_key = bool(settings.GROQ_API_KEY)
        print(f"  -> GROQ_API_KEY Configured: {has_key}")
    if ollama_provider:
        status = await get_ollama_status()
        print(f"  -> Ollama Reachable: {status['reachable']} (Model: {status['selected_model']})")
        
    print(f"Groq Circuit Breaker Healthy: {await cb.is_healthy('groq')}")
        
    print("\n--- RECENT CHAT REQUESTS ---")
    try:
        with SessionLocal() as db:
            last_event = db.query(Analytics).filter(
                Analytics.event_type == "llm_request"
            ).order_by(Analytics.created_at.desc()).first()
            
            if last_event:
                data = last_event.event_data
                print(f"Last Chat Request Handled By: {data.get('provider')}")
                print(f"Status: {data.get('status')}")
                print(f"Latency: {data.get('latency_ms')} ms")
                print(f"Time: {last_event.created_at}")
            else:
                print("No recent chat requests found in Analytics table.")
    except Exception as e:
        print(f"Error querying database: {e}")

if __name__ == "__main__":
    asyncio.run(inspect())
