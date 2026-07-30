from functools import lru_cache

from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def encode_text(text: str | list[str]) -> list[float] | list[list[float]]:
    return get_embedding_model().encode(text).tolist()


import asyncio

async def encode_text_async(text: str | list[str]) -> list[float] | list[list[float]]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, lambda: get_embedding_model().encode(text).tolist()
    )
