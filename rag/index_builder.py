# src/embeddings/index_builder.py
import json
import os
from pathlib import Path

import numpy as np

from .openai_client import embed_texts

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "opportunities"
INDICES_DIR = BASE_DIR / "indices"
INDICES_DIR.mkdir(parents=True, exist_ok=True)

INDEX_EMBEDDINGS_PATH = INDICES_DIR / "opportunities_index.npy"
INDEX_METADATA_PATH = INDICES_DIR / "opportunities_metadata.json"


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_all_opportunities() -> list[dict]:
    """
    Load all grants, vcs and accelerators into a single list.
    Each is expected to be a list of JSON objects.
    """
    all_ops: list[dict] = []

    for filename in ["grants.json", "vcs.json", "accelerators.json"]:
        file_path = DATA_DIR / filename
        if not file_path.exists():
            continue
        items = _load_json(file_path)
        # make sure each has a type (grant, vc, accelerator)
        for item in items:
            all_ops.append(item)

    return all_ops


def build_canonical_text_for_embedding(op: dict) -> str:
    """
    Turn an opportunity into a single text string to embed.
    You can tune this later.
    """
    title = op.get("title") or op.get("name") or ""
    summary = op.get("summary") or ""
    raw_text = op.get("raw_text") or ""
    region = ", ".join(op.get("region", []))
    caen_codes = ", ".join(op.get("eligible_caen_codes", []))
    op_type = op.get("type", "")

    return (
        f"Type: {op_type}\n"
        f"Title: {title}\n"
        f"Region: {region}\n"
        f"Eligible CAEN: {caen_codes}\n\n"
        f"Summary:\n{summary}\n\n"
        f"Full text:\n{raw_text}"
    )


def build_index():
    opportunities = load_all_opportunities()
    if not opportunities:
        raise RuntimeError("No opportunities found in data/opportunities/")

    texts = [build_canonical_text_for_embedding(op) for op in opportunities]

    print(f"Embedding {len(texts)} opportunities...")
    vectors = embed_texts(texts)
    embeddings = np.array(vectors, dtype="float32")

    # Save embeddings
    np.save(INDEX_EMBEDDINGS_PATH, embeddings)

    # Save metadata aligned with embeddings rows
    metadata = []
    for op in opportunities:
        metadata.append({
            "id": op["id"],
            "type": op.get("type", "unknown"),
            "title": op.get("title") or op.get("name"),
            "region": op.get("region", []),
            "eligible_caen_codes": op.get("eligible_caen_codes", []),
            "source_url": op.get("source_url"),
        })

    with INDEX_METADATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"Saved embeddings → {INDEX_EMBEDDINGS_PATH}")
    print(f"Saved metadata   → {INDEX_METADATA_PATH}")


if __name__ == "__main__":
    build_index()
