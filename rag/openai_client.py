# src/embeddings/openai_client.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # loads .env

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set in environment/.env")

client = OpenAI(api_key=OPENAI_API_KEY)

EMBEDDING_MODEL = "text-embedding-3-small"  # or -3-large if you want


def embed_text(text: str) -> list[float]:
    """
    Embed a single text string using OpenAI embeddings API.
    """
    resp = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[text],
    )
    return resp.data[0].embedding


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed multiple texts at once.
    """
    if not texts:
        return []
    resp = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [d.embedding for d in resp.data]
