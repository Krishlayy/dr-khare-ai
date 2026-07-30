import asyncio
import httpx
import sys

API_URL = "http://127.0.0.1:8000"

async def main():
    print("=== Testing All API Endpoints ===")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Test Root
        print("\n1. GET /")
        r = await client.get(f"{API_URL}/")
        print(f"Status: {r.status_code}")
        print(r.json())
        
        # 2. Test Auth Login
        print("\n2. POST /api/auth/login")
        data = {"username": "admin@khare.ai", "password": "admin123"}
        r = await client.post(f"{API_URL}/api/auth/login", data=data)
        print(f"Status: {r.status_code}")
        if r.status_code != 200:
            print("Failed to authenticate")
            sys.exit(1)
            
        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print("Obtained Bearer token successfully.")

        # 3. Test Admin Dashboard
        print("\n3. GET /api/admin/dashboard")
        r = await client.get(f"{API_URL}/api/admin/dashboard", headers=headers)
        print(f"Status: {r.status_code}")
        print(r.json())
        
        # 4. Test Admin Analytics
        print("\n4. GET /api/admin/analytics")
        r = await client.get(f"{API_URL}/api/admin/analytics", headers=headers)
        print(f"Status: {r.status_code}")
        print(r.json())

        # 5. Test Debug Chroma
        print("\n5. GET /api/debug/chroma")
        r = await client.get(f"{API_URL}/api/debug/chroma", headers=headers)
        print(f"Status: {r.status_code}")
        print(f"Documents indexed: {r.json().get('documents_count')}")
        
        # 6. Test Debug Ollama
        print("\n6. GET /api/debug/ollama")
        r = await client.get(f"{API_URL}/api/debug/ollama", headers=headers)
        print(f"Status: {r.status_code}")
        print(r.json())

        # 7. Test Chat Stream endpoint
        print("\n7. POST /api/chat/stream")
        r = await client.post(
            f"{API_URL}/api/chat/stream", 
            json={"text": "Hello, is the API working?", "session_id": "test_1"}
        )
        print(f"Status: {r.status_code}")
        print(r.json().get("response"))

    print("\n=== All Tests Completed ===")

if __name__ == "__main__":
    asyncio.run(main())
