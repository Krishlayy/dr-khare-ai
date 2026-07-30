"""
Diagnostic: Print the actual confidence scores for the first 20 questions
to understand why short-latency failures are triggering the hard grounding guard.
"""
import asyncio
import csv
from backend.rag.retrieval import retrieve_context
from backend.core.config import settings

async def main():
    questions = []
    with open("benchmark_results.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) >= 3:
                questions.append((row[1], row[2]))  # question, expected

    print(f"SIMILARITY_THRESHOLD = {settings.SIMILARITY_THRESHOLD}")
    print(f"{'Q':<5} {'Confidence':>12}  {'Pass Threshold':>14}  Question[:60]")
    print("-" * 95)

    for i, (q, expected) in enumerate(questions[:20]):
        result = await retrieve_context(q)
        above = "ABOVE" if result.confidence >= settings.SIMILARITY_THRESHOLD else "BELOW"
        print(f"{i+1:<5} {result.confidence:>12.4f}  {above:>14}  {q[:60]}")

if __name__ == "__main__":
    asyncio.run(main())
