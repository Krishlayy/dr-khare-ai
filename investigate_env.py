import os
from pathlib import Path
from backend.core.config import settings

def investigate():
    # 1. Exact path of the .env file being loaded by pydantic settings.
    # Pydantic Settings Config
    env_file = settings.model_config.get("env_file")
    
    exact_path = None
    if env_file:
        p = Path(env_file)
        if p.exists():
            exact_path = p.resolve()
        else:
            # Maybe it looks in current directory
            p = Path(os.getcwd()) / env_file
            if p.exists():
                exact_path = p.resolve()
    
    print(f"1. Exact path of env_file loaded: {exact_path} (Resolved from '{env_file}')")
    
    # 2. Whether GROQ_API_KEY exists in that file.
    exists_in_file = False
    if exact_path:
        with open(exact_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "GROQ_API_KEY=" in content:
                exists_in_file = True
    print(f"2. GROQ_API_KEY exists in that file: {exists_in_file}")
    
    # 3. Whether config.py contains a GROQ_API_KEY field.
    from pydantic.fields import FieldInfo
    has_field = "GROQ_API_KEY" in settings.model_fields
    print(f"3. config.py contains GROQ_API_KEY field: {has_field}")
    
    # 4. The value of settings.model_config.env_file
    print(f"4. settings.model_config['env_file'] value: {env_file}")
    
    # 5. The first 20 environment variables loaded by Settings (mask secrets)
    print("5. First 20 environment variables loaded by Settings:")
    count = 0
    for k, v in settings.model_dump().items():
        if count >= 20:
            break
        if "KEY" in k or "URL" in k or "SECRET" in k or "DSN" in k:
            val = "***MASKED***" if v else "None"
        else:
            val = v
        print(f"   {k}: {val}")
        count += 1
        
    # 6. Root cause
    # I will output data to determine the root cause.

if __name__ == "__main__":
    investigate()
