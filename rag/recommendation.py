# rag/recommendation.py (LLM-based ranking version)
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parents[1]
FIRMS_DIR = BASE_DIR / "data" / "firms"
OPP_DIR = BASE_DIR / "data" / "opportunities"

load_dotenv()

client = OpenAI()


def load_firm_by_cif(cif: str) -> Dict[str, Any]:
    path = FIRMS_DIR / f"{cif}.json"
    if not path.exists():
        raise FileNotFoundError(f"Firm file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_all_opportunities() -> Dict[str, Dict[str, Any]]:
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


def llm_match_score(firm: Dict[str, Any], opp: Dict[str, Any]) -> float:
    """
    Returns an LLM-evaluated compatibility score (0-1).
    """
    prompt = f"""
You are an expert evaluator.
Assign a semantic match score between a startup and a funding opportunity.
Score range: 0.0 = unrelated, 1.0 = perfect match.
Keep in mind that this score is used for deciding if the firm is eligible.
DO NOT give high scores for ineligible firms. If a firm is ineligible it should have a score lower than 0.5, and higher otherwise.
Respond ONLY with a JSON object: {{"score": float}}

Startup:
{json.dumps(firm, ensure_ascii=False, indent=2)}

Opportunity:
{json.dumps(opp, ensure_ascii=False, indent=2)}
"""
    resp = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        max_output_tokens=100,
    )
    text = resp.output_text
    try:
        data = json.loads(text)
        return float(data.get("score", 0.0))
    except Exception:
        return 0.0


def explain_match_llm(
    firm: Dict[str, Any], opp: Dict[str, Any], score: float
) -> List[str]:
    prompt = f"""
Explain why the following startup might match the funding opportunity.
Respond with a bullet point list.

Startup:
{json.dumps(firm, indent=2, ensure_ascii=False)}

Opportunity:
{json.dumps(opp, indent=2, ensure_ascii=False)}

Match score: {score}
"""
    resp = client.responses.create(
        model="gpt-4.1-nano",
        input=prompt,
        max_output_tokens=200,
    )
    text = resp.output_text
    return [line.strip("- ") for line in text.split("\n") if line.strip()]


def recommend_opportunities_for_firm(
    cif: str,
    top_k: int = 5,
    opp_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    firm = load_firm_by_cif(cif)
    all_opps = load_all_opportunities()

    # Optionally filter by type
    if opp_type:
        opportunities = [op for op in all_opps.values() if op.get("type") == opp_type]
    else:
        opportunities = list(all_opps.values())

    scored: List[Dict[str, Any]] = []

    for opp in opportunities:
        score = llm_match_score(firm, opp)
        reasons = explain_match_llm(firm, opp, score)
        scored.append(
            {
                "id": opp.get("id"),
                "type": opp.get("type"),
                "title": opp.get("title") or opp.get("name"),
                "semantic_score": score,
                "eligible": score >= 0.5,
                "region": opp.get("region", []),
                "eligible_caen_codes": opp.get("eligible_caen_codes", []),
                "deadlines": opp.get("deadlines", []),
                "eligibility_criteria": opp.get("eligibility_criteria", []),
                "number_of_docs": len(opp.get("required_documents", [])),
                "source_url": opp.get("source_url"),
                "funding": opp.get("funding_max", "unspecified"),
                "match_reasons": reasons,
            }
        )

    scored.sort(key=lambda x: x["semantic_score"], reverse=True)
    return scored[:top_k]


if __name__ == "__main__":
    example_cif = "33945221"
    recs = recommend_opportunities_for_firm(example_cif, top_k=5)
    for r in recs:
        print(f"{r['semantic_score']:.3f} | {r['type']} | {r['title']}")
        for reason in r["match_reasons"]:
            print("  -", reason)
        print()
