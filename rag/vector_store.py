# src/embeddings/vector_store.py
# Codul CAEN real Veridion 7022
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from .openai_client import embed_text

BASE_DIR = Path(__file__).resolve().parents[1]
INDICES_DIR = BASE_DIR / "indices"

INDEX_EMBEDDINGS_PATH = INDICES_DIR / "opportunities_index.npy"
INDEX_METADATA_PATH = INDICES_DIR / "opportunities_metadata.json"


class OpportunityVectorStore:
    def __init__(self):
        self.embeddings = None  # np.ndarray shape (N, D)
        self.metadata: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if not INDEX_EMBEDDINGS_PATH.exists() or not INDEX_METADATA_PATH.exists():
            raise RuntimeError("Index files not found. Run index_builder.build_index() first.")

        self.embeddings = np.load(INDEX_EMBEDDINGS_PATH)
        with INDEX_METADATA_PATH.open("r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        if self.embeddings.shape[0] != len(self.metadata):
            raise RuntimeError("Embeddings and metadata size mismatch")

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_type: Optional[str] = None,
        filter_caen: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for opportunities similar to the query.
        Optionally filter by type ('grant', 'vc', 'accelerator') and/or CAEN code.
        """
        query_vec = np.array(embed_text(query), dtype="float32")

        # apply filters by masking metadata
        indices = list(range(len(self.metadata)))
        if filter_type:
            indices = [
                i for i in indices
                if self.metadata[i].get("type") == filter_type
            ]
        if filter_caen:
            indices = [
                i for i in indices
                if filter_caen in self.metadata[i].get("eligible_caen_codes", []) or len(self.metadata[i].get("eligible_caen_codes", [])) == 0
            ]

        if not indices:
            return []

        # slice embeddings
        sub_embeddings = self.embeddings[indices]

        # cosine similarity
        dots = sub_embeddings @ query_vec
        norms = np.linalg.norm(sub_embeddings, axis=1) * np.linalg.norm(query_vec)
        sims = dots / (norms + 1e-10)

        # top_k on the filtered indices
        top_k = min(top_k, len(indices))
        top_idx = np.argsort(-sims)[:top_k]

        results = []
        for rank_pos in top_idx:
            original_idx = indices[rank_pos]
            results.append({
                **self.metadata[original_idx],
                "score": float(sims[rank_pos]),
                "eligible": float(sims[rank_pos]) >= 0.40
            })

        return results

if __name__ == "__main__":
    store = OpportunityVectorStore()
    results = store.search(
        "grant pentru firmă de consultanță cu CAEN 7022",
        top_k=3,
        filter_type="grant",
        filter_caen="7022",
    )
    for r in results:
        print(f"{r['score']:.3f} | {r['type']} | {r['title']}")
