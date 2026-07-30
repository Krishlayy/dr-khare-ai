"""End-to-end pipeline verification: upload → retrieve → answer."""
import asyncio
import os
import sys
import tempfile

import httpx

BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")


async def main() -> int:
    print("E2E PIPELINE VERIFICATION")
    print("=" * 50)

    async with httpx.AsyncClient(timeout=180.0) as client:
        login = await client.post(
            f"{BASE}/api/auth/login",
            data={"username": "admin@khare.ai", "password": "admin123"},
        )
        if login.status_code != 200:
            print("FAIL: Login", login.status_code, login.text)
            return 1
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        content = (
            "Dr. Supreet Khare is a board-certified physician. "
            "Office hours: Monday to Friday 9am to 5pm. "
            "Education: MD from Stanford University, residency at Johns Hopkins."
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp_path = f.name

        try:
            with open(tmp_path, "rb") as fh:
                upload = await client.post(
                    f"{BASE}/api/upload",
                    files={"file": ("e2e_test.txt", fh, "text/plain")},
                    headers=headers,
                )
            print("Upload:", upload.status_code, upload.json())

            doc_id = upload.json()["document_id"]
            for _ in range(60):
                status = await client.get(
                    f"{BASE}/api/upload/status/{doc_id}", headers=headers
                )
                data = status.json()
                if data["status"] in ("completed", "failed"):
                    print("Processing:", data["status"], data["chunks_count"])
                    break
                await asyncio.sleep(1)

            retrieve = await client.post(
                f"{BASE}/api/debug/retrieve",
                headers=headers,
                json={"query": "What are Dr Khare office hours?"},
            )
            rdata = retrieve.json()
            print("Retrieve matches:", len(rdata["matches"]))
            print("Top score:", rdata["matches"][0]["score"] if rdata["matches"] else 0)
            print("Context preview:", rdata["context_preview"][:100])

            chat = await client.post(
                f"{BASE}/api/chat/stream",
                json={
                    "text": "What are Dr Khare office hours?",
                    "stream": False,
                },
            )
            cdata = chat.json()
            print("Chat source:", cdata.get("answer_source"))
            print("Chat confidence:", cdata.get("confidence"))
            print("Chat response:", cdata.get("response", "")[:200])
            print("Citations:", len(cdata.get("sources", [])))

            ollama = await client.get(f"{BASE}/api/debug/ollama", headers=headers)
            print("Ollama:", ollama.json())

            if not rdata["matches"]:
                print("\nFAIL: No retrieval matches")
                return 1
            if rdata["matches"][0]["score"] < 0.35:
                print("\nFAIL: Retrieval score too low")
                return 1
            if "could not find" in cdata.get("response", "").lower():
                print("\nFAIL: Chat returned no-context message")
                return 1

            print("\nPASS: End-to-end pipeline verified")
            return 0
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
