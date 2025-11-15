# src/rag/retrieval.py
from typing import List, Dict, Any, Optional

from vector_store import OpportunityVectorStore


class RAGRetriever:
    def __init__(self):
        self.store = OpportunityVectorStore()

    def retrieve_opportunities_for_query(
        self,
        query: str,
        *,
        caen_code: Optional[str] = None,
        opp_type: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        High-level retrieval for user-facing search.
        """
        return self.store.search(
            query=query,
            top_k=top_k,
            filter_type=opp_type,
            filter_caen=caen_code,
        )
