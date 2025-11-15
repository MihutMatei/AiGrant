# rag/documentation_rag.py
import json
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from openai import OpenAI

# Load env vars from .env in project root
load_dotenv()
client = OpenAI()  # uses OPENAI_API_KEY from env


# Project root: /.../AiGrant
BASE_DIR = Path(__file__).resolve().parents[1]
FIRMS_DIR = BASE_DIR / "data" / "firms"
OPP_DIR = BASE_DIR / "data" / "opportunities"


def load_firm_by_cif(cif: str) -> Dict[str, Any]:
    """
    Load firm JSON by CIF from data/firms/{cif}.json
    """
    path = FIRMS_DIR / f"{cif}.json"
    if not path.exists():
        raise FileNotFoundError(f"Firm file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_opportunity_by_id(opportunity_id: str) -> Dict[str, Any]:
    """
    Simple linear scan over grants/vcs/accelerators.
    For PoC this is fine.
    """
    for fname in ["grants.json", "vcs.json", "accelerators.json"]:
        path = OPP_DIR / fname
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as f:
            items = json.load(f)
        if isinstance(items, dict):
            items = [items]
        for op in items:
            if op.get("id") == opportunity_id:
                return op
    raise KeyError(f"Opportunity {opportunity_id} not found")


def build_docs_prompt(firm: Dict[str, Any], opp: Dict[str, Any]) -> str:
    """
    Builds the user prompt content to send to the model.
    """
    firm_name = firm.get("denumire")
    caen_descriere = firm.get("caen_descriere")
    cifra_afaceri = firm.get("cifra_de_afaceri_neta")
    profit_net = firm.get("profit_net")
    year = firm.get("year")

    opp_title = opp.get("title") or opp.get("name")
    opp_type = opp.get("type")
    raw_text = opp.get("raw_text") or ""
    eligibility_criteria = opp.get("eligibility_criteria", [])

    # Handle required docs as either list of dicts (required_documents_full)
    # or list of strings (required_documents)
    required_docs_raw = (
        opp.get("required_documents_full")
        or opp.get("required_documents", [])
    )

    if required_docs_raw and isinstance(required_docs_raw[0], dict):
        required_docs_list = [
            d.get("name", d.get("id", str(d))) for d in required_docs_raw
        ]
    else:
        required_docs_list = required_docs_raw

    eligibility_str = "\n".join(f"- {c}" for c in eligibility_criteria)
    required_docs_str = "\n".join(f"- {d}" for d in required_docs_list)

    return f"""
You are helping a Romanian company prepare documentation to apply for an opportunity.

=== Firm info ===
Name: {firm_name}
CAEN description: {caen_descriere}
Turnover (cifra de afaceri neta) {year}: {cifra_afaceri}
Profit net {year}: {profit_net}

=== Opportunity info ===
Type: {opp_type}
Title: {opp_title}

Raw description (official text):
\"\"\"
{raw_text}
\"\"\"

Eligibility criteria:
{eligibility_str}

Required documents (raw list):
{required_docs_str}

Task:
1. Generate a short summary (max 150 words) of why this company could be a good fit for this opportunity, based only on the firm info and the opportunity description.
2. Generate a checklist of documents the company must prepare, clearly separating:
   - documents that must be obtained from institutions (e.g. ONRC)
   - documents that can be drafted with AI and then reviewed by the founder.
3. Generate a structured JSON response with the following keys:
   - "summary": string
   - "ai_generatable_docs": list of strings (names)
   - "institutional_docs": list of strings (names)
   - "extra_notes": string
4. Generate all the documents that can be drafted with AI as text inside json fields with the name of the generated doc type
Use Romanian language in the content of the fields, but keep the JSON keys in English.
Return ONLY valid JSON, no explanation.
    """.strip()


def generate_docs_package(cif: str, opportunity_id: str) -> Dict[str, Any]:
    """
    Main entry: given firm CUI and opportunity id, call OpenAI to get
    a structured 'application package' JSON we can feed into the PDF builder.
    """
    firm = load_firm_by_cif(cif)
    opp = load_opportunity_by_id(opportunity_id)

    user_prompt = build_docs_prompt(firm, opp)

    resp = client.chat.completions.create(
        model="gpt-4.1-mini",  # you can change this to another model if you want
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant specialized in Romanian startup "
                    "grants, accelerators and investments. You always respond with "
                    "valid JSON when asked."
                ),
            },
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    content = resp.choices[0].message.content
    # content is a JSON string because of response_format
    package = json.loads(content)
    return package


if __name__ == "__main__":
    # Example usage: test with your mock firm + mock grant
    example_cif = "33945221"
    example_opp_id = "grant_ro_mock_1"  # must match the id in grants.json

    result_package = generate_docs_package(example_cif, example_opp_id)
    print(json.dumps(result_package, ensure_ascii=False, indent=2))
