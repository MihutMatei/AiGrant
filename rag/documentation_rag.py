# rag/documentation_rag.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()  # folosește OPENAI_API_KEY din .env

BASE_DIR = Path(__file__).resolve().parents[1]
FIRMS_DIR = BASE_DIR / "data" / "firms"
OPP_DIR = BASE_DIR / "data" / "opportunities"


def load_firm_by_cif(cif: str) -> Dict[str, Any]:
    path = FIRMS_DIR / f"{cif}.json"
    if not path.exists():
        raise FileNotFoundError(f"Firm file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_opportunity_by_id(opportunity_id: str) -> Dict[str, Any]:
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
    Prompt pentru generarea unui pachet JSON cu:
    - summary
    - ai_docs (draft-uri detaliate)
    - institutional_docs (ce nu poate fi generat, de unde se ia)
    - questions_for_user
    - to_improve
    - extra_notes
    """
    firm_name = firm.get("denumire")
    caen_descriere = firm.get("caen_descriere")
    caen_code = firm.get("caen_code")
    cifra_afaceri = firm.get("cifra_de_afaceri_neta")
    profit_net = firm.get("profit_net")
    year = firm.get("year")

    opp_title = opp.get("title") or opp.get("name")
    opp_type = opp.get("type")
    raw_text = opp.get("raw_text") or ""
    eligibility_criteria = opp.get("eligibility_criteria", [])

    required_docs_struct = opp.get("required_documents_full") or []
    if not required_docs_struct and opp.get("required_documents"):
        # fallback: listă simplă de string-uri
        required_docs_struct = [
            {
                "id": f"doc_{i}",
                "name": name,
                "description": "",
                "ai_can_generate": True,  # presupunem că se pot genera
            }
            for i, name in enumerate(opp["required_documents"])
        ]

    # Formatare frumoasă pentru prompt
    eligibility_str = "\n".join(f"- {c}" for c in eligibility_criteria)

    docs_lines = []
    for d in required_docs_struct:
        docs_lines.append(
            f"- id: {d.get('id')}, "
            f"name: {d.get('name')}, "
            f"ai_can_generate: {d.get('ai_can_generate')}, "
            f"description: {d.get('description', '')}"
        )
    required_docs_str = "\n".join(docs_lines)

    return f"""
# Rol si obiectiv

Ești un asistent specializat în documentație pentru granturi, VC și acceleratoare pentru IMM-uri din România.

# Instructiuni

Ți se dau informații despre o firmă și o oportunitate (grant/VC/accelerator).
Generează documente conform instrucțiunilor de mai jos.

Reguli:
- Pentru fiecare document, vei scrie între 1 și 3 pagini (aproximativ 600-1800 cuvinte) de text coerent, profesionist și complet.
- Nu scrie meta-explicații, nu comenta, nu adăuga text exterior cerințelor.
- Tot conținutul trebuie să fie parsabil, fără bullet point-uri goale sau fraze neterminate.
- Dacă lipsesc informații, folosește placeholderul [DE COMPLETAT].
- Respectă delimitările EXACT cum sunt definite.
- Folosește DOAR informațiile primite; dacă lipsesc date (ex: suma exactă a proiectului, durata), folosește placeholdere clare de tipul "[DE COMPLETAT]" în draft.
- Pentru fiecare document unde "ai_can_generate" = true, creează un element în "ai_docs" cu draft detaliat.
  - Pentru "Plan de Afaceri": include secțiuni standard: Rezumat executiv, Descrierea companiei, Analiza pieței, Produse/Servicii, Strategie și implementare, Management și echipă, Plan financiar, Riscuri.
  - Pentru "Dovada Cofinanțării": generează un text formal de declarație.
- Pentru documentele unde "ai_can_generate" = false, adaugă-le în "institutional_docs" și indică sursa probabilă:
  - Dacă numele sau descrierea conține "certificat constatator" sau "ONRC" → recommended_source = "ONRC".
  - Dacă conține "situații financiare", "bilanț", "ANAF" → recommended_source = "ANAF/contabil".
  - Dacă conține "extras de cont", "cont bancar" → recommended_source = "Bancă".
  - Altfel → "Alte autorități".
- Toate textele (titluri, draft-uri) trebuie să fie în limba română.
- Cheile JSON trebuie să fie EXACT cele specificate mai jos.
- Răspunsul trebuie să fie DOAR JSON valid, fără alt text.
- Foloseste un limbaj cat mai adecvat din punct de vedere legal.

# Formatul cerut

Trebuie să generezi un răspuns STRICT în format JSON, cu următoarea structură:

{{
  "ai_docs": [
    {{
      "name": string,
      "type": string,  // ex: "business_plan", "cofinancing_declaration", "other"
      "draft": // continutul propriu-zis al documentului, impartit pe sectiuni
      [
        {{
            "title": string, // titlul primei sectiuni (ex. "Rezumat executiv", "Descrierea afacerii", "Strategia de marketing", "Plan operational")
            "body": string // corpul sectiunii
        }},
        {{
            "title": string, // titlul celei de-a doua sectiuni
            "body": string // corpul sectiunii
        }},
        ... // atatea sectiuni cat sunt necesare conform cerintelor de finantare si descrierii companiei
      ]
    }}
  ],
  "institutional_docs": [
    {{
      "name": string,
      "recommended_source": string,  // ex: "ONRC", "ANAF/contabil", "Bancă", "Alte autorități"
      "note": string  // explicație scurtă
    }}
  ]
}}

# Documentele generate

Documentele de generat sunt: "Plan de Afaceri", "Dovada Cofinantarii", "Scrisoare de Intentie".
Nu scrie nimic altceva decat aceste documente.

# Date despre firma

Nume: {firm_name}
Cod CAEN: {caen_code} ({caen_descriere})
Cifră de afaceri netă {year}: {cifra_afaceri}
Profit net {year}: {profit_net}

# Date despre oportunitatea de finantare

Tip: {opp_type}
Titlu: {opp_title}

Eligibilitate (bullet-uri):
{eligibility_str}

Documente cerute (structurate):
{required_docs_str}

Text oficial / descriere completă:
\"\"\"
{raw_text}
\"\"\"

# Reguli importante
 - Pentru fiecare document scrie cel putin 600 cuvinte.
 - Respecta EXACT formatul mentionat mai sus.
 - Nu genera altceva decat ce este specificat mai sus.
- Foloseste un limbaj cat mai adecvat din punct de vedere legal.
    """.strip()


def generate_docs_package(cif: str, opportunity_id: str) -> Dict[str, Any]:
    """
    Generează un pachet JSON cu toate informațiile necesare pentru documentație:
    - summary
    - ai_docs (drafturi)
    - institutional_docs
    - questions_for_user
    - to_improve
    - extra_notes
    """
    firm = load_firm_by_cif(cif)
    opp = load_opportunity_by_id(opportunity_id)

    user_prompt = build_docs_prompt(firm, opp)

    resp = client.chat.completions.create(
        model="gpt-4.1",  # modelul pe care îl folosești în proiect
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a JSON-only assistant. "
                    "You ALWAYS respond with valid JSON that matches the requested schema."
                ),
            },
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    content = resp.choices[0].message.content
    package = json.loads(content)

    # mică siguranță: asigurăm câmpurile de bază
    package.setdefault("summary", "")
    package.setdefault("ai_docs", [])
    package.setdefault("institutional_docs", [])
    package.setdefault("questions_for_user", [])
    package.setdefault("to_improve", [])
    package.setdefault("extra_notes", "")

    return package


if __name__ == "__main__":
    example_cif = "33945221"
    example_opp_id = "grant_ro_mock_1"  # id-ul tău de test

    package = generate_docs_package(example_cif, example_opp_id)
    print(json.dumps(package, ensure_ascii=False, indent=2))
