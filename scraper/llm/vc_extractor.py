from llm.base_extractor import BaseExtractor
import json

VC_SCHEMA = json.dumps({
  "id": "string",
  "type": "grant | vc | accelerator",
  "title": "string | null",

  "source_url": "string",

  "region": ["string"],
  "eligible_countries": ["string"],
  "eligible_caen_codes": ["string"],

  "raw_text": "string",
  "summary": "string",

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

  "application_format": "pitchdeck | online_form | portal | pdf_upload | email",
  "application_language": "ro | en",

  "team_information_required": "boolean",
  "financials_required": "boolean",
  "traction_required": "boolean",
  "budget_template_required": "boolean",

  "deadlines": [
    {
      "label": "string",
      "date": "string | null"
    }
  ],

  "additional_notes": "string | null"
})

class VCExtractor(BaseExtractor):
    def __init__(self):
        super().__init__("prompts/extract_vc.txt", VC_SCHEMA)
