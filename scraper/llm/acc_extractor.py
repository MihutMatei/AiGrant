from llm.base_extractor import BaseExtractor
import json

ACCEL_SCHEMA = json.dumps({
  "id": "string",
  "type": "accelerator",

  "name": "string",
  "cohort_name": "string | null",
  "source_url": "string",

  "region": ["string"],
  "eligible_countries": ["string"],
  "eligible_caen_codes": ["string"],

  "equity_taken": "boolean",
  "equity_percentage": "number | null",
  "cash_stipend": "number | null",
  "currency": "string | null",

  "program_duration_months": "number",
  "program_location": "string",
  "program_format": "online | offline | hybrid",

  "summary": "string",
  "raw_text": "string",

  "eligibility_criteria": ["string"],
  "required_documents": ["string"],
  "required_documents_full": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "ai_can_generate": "boolean",
      "official_template_url": "string | null",
      "format": ["string"]
    }
  ],

  "application_format": "online_form | portal | pitchdeck | email",
  "application_portal_name": "string | null",
  "application_language": "en | ro",

  "team_information_required": "boolean",
  "financials_required": "boolean",
  "traction_required": "boolean",
  "budget_template_required": "boolean",

  "deadlines": [
    {
      "label": "string",
      "date": "string"
    }
  ],

  "additional_notes": "string | null"
})

class AcceleratorExtractor(BaseExtractor):
    def __init__(self):
        super().__init__("prompts/extract_acc.txt", ACCEL_SCHEMA)
