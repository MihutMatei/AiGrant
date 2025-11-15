from typing import List, Dict, Any, Optional
from .vector_store import OpportunityVectorStore

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
        return self.store.search(
            query=query,
            top_k=top_k,
            filter_type=opp_type,
            filter_caen=caen_code,
        )

if __name__ == "__main__":
    r = RAGRetriever()
    results = r.retrieve_opportunities_for_query(
        "grant pentru digitalizare pentru firmă de consultanță",
        caen_code="7022",
        opp_type="grant",
        top_k=3,
    )
    for x in results:
        print(f"{x['score']:.3f} | {x['type']} | {x['title']}")
