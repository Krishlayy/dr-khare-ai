import os
import asyncio
from backend.core.config import settings
from backend.services.llm_service import _providers, cb

async def verify():
    # 1. Active ENV_FILE value
    env_file = os.environ.get("ENV_FILE", ".env (default)")
    print(f"1. Active ENV_FILE value: {env_file}")
    
    # 2. Whether GROQ_API_KEY is loaded into settings
    has_key = bool(settings.GROQ_API_KEY)
    print(f"2. GROQ_API_KEY loaded: {has_key}")
    
    # 3. Length of GROQ_API_KEY
    key_length = len(settings.GROQ_API_KEY) if settings.GROQ_API_KEY else 0
    print(f"3. GROQ_API_KEY length: {key_length}")
    
    # 4. Whether a live Groq API request succeeds
    groq_provider = _providers.get("groq")
    success = False
    if has_key and groq_provider:
        try:
            print("   -> Testing live Groq API request...")
            res = await groq_provider.generate("Say 'Hello' and nothing else.", temperature=0.0)
            if res:
                success = True
                print("   -> Live request successful!")
        except Exception as e:
            print(f"   -> Live request failed: {e}")
    else:
        print("   -> Skipping live test (no API key configured).")
    
    print(f"4. Live Groq API request succeeds: {success}")
    
    # 5. Which provider would handle a chat request right now
    primary = settings.PRIMARY_PROVIDER
    fallback = settings.FALLBACK_PROVIDER
    
    is_primary_healthy = await cb.is_healthy(primary)
    
    if primary == "groq" and not has_key:
        print("   -> Primary provider is 'groq' but no key is present. The circuit is open/broken.")
        handled_by = fallback
    elif is_primary_healthy:
        handled_by = primary
    else:
        handled_by = fallback
        
    print(f"5. Provider handling chat requests right now: {handled_by}")

if __name__ == "__main__":
    asyncio.run(verify())
