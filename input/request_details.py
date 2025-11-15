#!/usr/bin/env python3
"""
Fetch company details and balances from OpenAPI.ro based on TAX_CODE.
Outputs a flattened JSON file with combined data.

Usage:
    python request.py <TAX_CODE>
Return:
    1 on success, 0 on failure.
"""

import requests
import os
import json
import sys
import logging
from datetime import datetime
from typing import Any, Dict

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def flatten(prefix: str, obj: Any, out: Dict[str, Any]) -> None:
    """
    Recursively flatten nested dictionaries and lists.

    Args:
        prefix (str): Prefix for nested keys.
        obj (Any): The current object to flatten (dict, list, or primitive).
        out (dict): Output dictionary to store flattened results.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            flatten(f"{prefix}_{k}" if prefix else k, v, out)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            flatten(f"{prefix}_{i}", item, out)
    else:
        out[prefix] = obj

def fetch_json(url: str, headers: Dict[str, str]) -> dict:
    """
    Fetch JSON from a URL with error handling.

    Args:
        url (str): API endpoint.
        headers (dict): HTTP headers.

    Returns:
        dict: Parsed JSON response, empty dict on failure.
    """
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise for HTTP errors
        return response.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        logging.warning(f"Failed to fetch {url}: {e}")
        return {}

def main() -> int:
    """Main entry point of the script."""
    if len(sys.argv) < 2:
        logging.error("Usage: python request.py <TAX_CODE>; returns 1 if success, 0 if failure.")
        return 0

    TAX_CODE = sys.argv[1]
    OPENAPI_KEY = os.getenv("OPENAPI_KEY", "QxTiAi7jaP7HLLuvU7fWjxUJW3GyKLpJ4yUG9gHVnTuEFSCKPQ")

    BASE_URL = "https://api.openapi.ro/api/companies/{tax_code}/"
    BASE_URL_COMPLETE = "https://api.openapi.ro/api/companies/{tax_code}/balances/{year}"
    headers = {"x-api-key": OPENAPI_KEY}

    # Step 1: Fetch basic company info
    logging.info(f"Fetching company info for TAX_CODE={TAX_CODE}")
    company_data = fetch_json(BASE_URL.format(tax_code=TAX_CODE), headers)
    if not company_data or "error" in company_data:
        logging.error("Failed to fetch valid company data.")
        return 0

    # Step 2: Fetch balances for last 5 years
    current_year = datetime.now().year
    balances_data = {}
    for i in range(5):
        year = current_year - i
        logging.info(f"Attempting to fetch balances for year {year}")
        data = fetch_json(BASE_URL_COMPLETE.format(tax_code=TAX_CODE, year=year), headers)
        if data and "error" not in data:
            balances_data = data
            logging.info(f"Balances found for year {year}")
            break

    if not balances_data:
        logging.error("No valid balances data found for the last 5 years.")
        return 0

    # Step 3: Flatten and merge data
    flattened_data = {}
    for k, v in company_data.items():
        if k != "meta":
            flatten(k, v, flattened_data)

    if "data" in balances_data:
        for k, v in balances_data["data"].items():
            flatten(k, v, flattened_data)

    for k in ["year", "balance_type", "caen_code"]:
        if k in balances_data:
            flattened_data[k] = balances_data[k]

    # Step 4: Save to JSON file
    details_filename = f"{TAX_CODE}_details.json"
    try:
        with open(details_filename, "w", encoding="utf-8") as f:
            json.dump(flattened_data, f, ensure_ascii=False, indent=4)
        logging.info(f"Data saved to {details_filename}")
    except Exception as e:
        logging.error(f"Failed to save JSON file: {e}")
        return 0

    return 1

if __name__ == "__main__":
    sys.exit(main())
