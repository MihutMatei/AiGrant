from llm.base_extractor import BaseExtractor
import json

ACCEL_SCHEMA = json.dumps({
  "id": "string",
  "type": "accelerator",
  "name": "string",
  "cohort_name": "string",
  "source_url": "string",
  "region": ["string"],
  "eligible_countries": ["string"],
  "eligible_caen_codes": ["string"],
  "equity_taken": False,
  "equity_percentage": 0.0,
  "cash_stipend": 0,
  "currency": "string",
  "program_duration_months": 0,
  "program_location": "string",
  "program_format": "string",
  "summary": "string",
  "raw_text": "string",
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

class AcceleratorExtractor(BaseExtractor):
    def __init__(self):
        super().__init__("prompts/extract_acc.txt", ACCEL_SCHEMA)
