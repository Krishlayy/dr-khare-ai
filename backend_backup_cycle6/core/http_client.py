import httpx

client: httpx.AsyncClient | None = None

def get_client() -> httpx.AsyncClient:
    global client
    if client is None:
        client = httpx.AsyncClient(timeout=300.0)
    return client

async def close_client():
    global client
    if client is not None:
        await client.aclose()
        client = None
