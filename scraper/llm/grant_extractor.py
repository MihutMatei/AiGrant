from llm.base_extractor import BaseExtractor
import json

GRANT_SCHEMA = json.dumps({
  "id": "string",
  "type": "grant",
  "title": "string",
  "source_url": "string",
  "region": ["string"],
  "eligible_countries": ["string"],
  "eligible_caen_codes": ["string"],
  "funding_min": 0,
  "funding_max": 0,
  "funding_currency": "string",
  "non_dilutive": True,
  "cofinancing_required": True,
  "cofinancing_min_ratio": 0.0,
  "raw_text": "string",
  "summary": "string",
  "eligibility_criteria": ["string"],
  "required_documents": ["string"],
  "required_documents_full": [],
  "application_format": "string",
  "application_language": "string",
  "team_information_required": False,
  "financials_required": False,
  "traction_required": False,
  "budget_template_required": False,
  "deadlines": [],
  "additional_notes": "string"
})

class GrantExtractor(BaseExtractor):
    def __init__(self):
        super().__init__("prompts/extract_grant.txt", GRANT_SCHEMA)
