import asyncio
from backend.services.chat_service import process_chat
from backend.database.database import SessionLocal

async def main():
    db = SessionLocal()
    q = "What is Dr. Khare's preferred phone number?"
    print(f"Querying: {q}")
    resp = await process_chat(db, q, "validation_run")
    print(resp)
    db.close()

if __name__ == "__main__":
    asyncio.run(main())
