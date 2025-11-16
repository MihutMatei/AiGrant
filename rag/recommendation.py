# rag/recommendation.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .vector_store import OpportunityVectorStore

BASE_DIR = Path(__file__).resolve().parents[1]
FIRMS_DIR = BASE_DIR / "data" / "firms"
OPP_DIR = BASE_DIR / "data" / "opportunities"


def load_firm_by_cif(cif: str) -> Dict[str, Any]:
    path = FIRMS_DIR / f"{cif}.json"
    if not path.exists():
        raise FileNotFoundError(f"Firm file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_all_opportunities() -> Dict[str, Dict[str, Any]]:
    """
    Returnează un dict {id: opportunity_dict} cu toate granturile/VC/acceleratoarele.
    """
    by_id: Dict[str, Dict[str, Any]] = {}
    for fname in ["sources.json"]:
        path = OPP_DIR / fname
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as f:
            items = json.load(f)
        all_opps = []
        for opp_type in ["grants", "accelerators", "vcs"]:
            all_opps = all_opps + items.get(opp_type, [])
        for op in all_opps:
            op_id = op.get("id")
            if op_id:
                by_id[op_id] = op
    return by_id


def build_firm_query(firm: Dict[str, Any]) -> str:
    """
    Construiește un query text din info despre firmă pentru semantic search.
    """
    name = firm.get("denumire") or ""
    caen_code = str(firm.get("caen_code") or "")
    caen_descriere = firm.get("caen_descriere") or ""
    cifra = firm.get("cifra_de_afaceri_neta")
    profit = firm.get("profit_net")
    year = firm.get("year")

    return (
        f"Firmă românească (IMM) numită {name}, "
        f"cu cod CAEN {caen_code} ({caen_descriere}), "
        f"cifră de afaceri {cifra} lei și profit net {profit} în {year}. "
        f"Interesată de granturi, fonduri VC sau acceleratoare relevante pentru acest profil."
    )


def explain_match(
    firm: Dict[str, Any],
    opp: Dict[str, Any],
    semantic_score: float,
) -> List[str]:
    """
    Generează explicații simple, rule-based, pentru de ce oportunitatea pare potrivită.
    Nu folosim LLM aici, doar logică simplă.
    """
    reasons: List[str] = []

    firm_caen = str(firm.get("caen_code") or "")
    eligible_caen = opp.get("eligible_caen_codes", []) or []
    if firm_caen and firm_caen in eligible_caen:
        reasons.append(f"Codul CAEN {firm_caen} al firmei este în lista de CAEN eligibile.")
    elif eligible_caen:
        reasons.append(
            f"Codul CAEN {firm_caen} nu apare explicit în lista eligibilă {eligible_caen}, "
            "dar există asemănare semantică (scor de similaritate bun)."
        )

    eligible_countries = opp.get("eligible_countries", []) or []
    if not eligible_countries or "Romania" in eligible_countries:
        reasons.append("Oportunitatea este deschisă companiilor din România.")
    else:
        reasons.append(
            f"Oportunitatea pare orientată spre {eligible_countries}; verifică eligibilitatea pentru România."
        )

    opp_type = opp.get("type")
    if opp_type == "grant":
        reasons.append("Este un grant (finanțare nerambursabilă).")
    elif opp_type == "vc":
        reasons.append("Este un fond de investiții (VC).")
    elif opp_type == "accelerator":
        reasons.append("Este un program de accelerare.")

    if opp.get("non_dilutive") is True:
        reasons.append("Finanțarea este nedilutivă (nu presupune cedare de equity).")

    cifra = firm.get("cifra_de_afaceri_neta")
    if cifra:
        reasons.append(
            "Firma are deja cifră de afaceri, ceea ce ajută la demonstrarea capacității financiare."
        )

    reasons.append(f"Scor de similaritate semantică (RAG): {semantic_score:.3f}.")

    return reasons


def recommend_opportunities_for_firm(
    cif: str,
    top_k: int = 5,
    opp_type: Optional[str] = None,  # "grant" | "vc" | "accelerator" | None
) -> List[Dict[str, Any]]:
    """
    Returnează top_k cele mai potrivite oportunități pentru firma cu CIF dat,
    folosind informația din firmă + indexul vectorial.
    """
    firm = load_firm_by_cif(cif)
    all_opps = load_all_opportunities()
    store = OpportunityVectorStore()

    firm_query = build_firm_query(firm)
    firm_caen = str(firm.get("caen_code") or "")

    # Căutare semantică filtrată pe CAEN (dacă îl avem)
    results_meta = store.search(
        query=firm_query,
        top_k=top_k * 3,  # luăm mai multe, apoi reordonăm
        filter_type=opp_type,
        filter_caen=firm_caen or None,
    )

    recommendations: List[Dict[str, Any]] = []
    for meta in results_meta:
        op_id = meta["id"]
        opp = all_opps.get(op_id)
        if not opp:
            continue

        semantic_score = meta.get("score", 0.0)
        reasons = explain_match(firm, opp, semantic_score)

        recommendations.append(
            {
                "id": op_id,
                "type": opp.get("type"),
                "title": opp.get("title") or opp.get("name"),
                "semantic_score": semantic_score,
                "eligibility": meta.get("eligible"),
                "match_reasons": reasons,
                "source_url": opp.get("source_url"),
            }
        )

    # Sortăm după scor semantic descrescător
    recommendations.sort(key=lambda x: x["semantic_score"], reverse=True)

    return recommendations[:top_k]


if __name__ == "__main__":
    # Test simplu pentru firma ta mock
    example_cif = "33945221"
    recs = recommend_opportunities_for_firm(example_cif, top_k=5, opp_type=None)
    for r in recs:
        print(f"{r['semantic_score']:.3f} | {r['type']} | {r['title']}")
        for reason in r["match_reasons"]:
            print("  -", reason)
        print()
