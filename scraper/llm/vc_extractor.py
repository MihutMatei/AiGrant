from llm.base_extractor import BaseExtractor
import json

VC_SCHEMA = json.dumps({
  "id": "string",
  "type": "vc",
  "title": "string",
  "source_url": "string",
  "region": ["string"],
  "investment_thesis": "string",
  "ticket_size_min": 0,
  "ticket_size_max": 0,
  "ticket_currency": "string",
  "stage_focus": ["string"],
  "sector_focus": ["string"],
  "eligibility_criteria": ["string"],
  "raw_text": "string",
  "summary": "string",
  "additional_notes": "string"
})

class VCExtractor(BaseExtractor):
    def __init__(self):
        super().__init__("prompts/extract_vc.txt", VC_SCHEMA)
