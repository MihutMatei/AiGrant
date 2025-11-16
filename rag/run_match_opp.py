# rag/run_match_opportunities.py
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .recommendation import recommend_opportunities_for_firm

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(
        description="Match opportunities for a given firm CIF."
    )
    parser.add_argument("--cif", required=True, help="CIF-ul firmei (ex: 33945221)")
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Numărul de oportunități recomandate (default 5).",
    )
    parser.add_argument(
        "--type",
        choices=["grant", "vc", "accelerator", "all"],
        default="all",
        help="Filtru pe tipul oportunităților.",
    )

    args = parser.parse_args()
    cif = args.cif
    top_k = args.top_k
    opp_type = None if args.type == "all" else args.type

    recs = recommend_opportunities_for_firm(cif, top_k=top_k, opp_type=opp_type)

    # Print to stdout
    print(json.dumps(recs, ensure_ascii=False, indent=2))

    # Also save to file for debugging / frontend
    firm_dir = OUTPUT_DIR / cif
    firm_dir.mkdir(parents=True, exist_ok=True)
    out_path = firm_dir / f"match_opportunities_top_{top_k}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False, indent=2)

    print(f"\n[info] Saved matches to {out_path}")


if __name__ == "__main__":
    main()
