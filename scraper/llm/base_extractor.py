import openai
import json
import os

class BaseExtractor:
    def __init__(self, prompt_path, schema_json):
        self.prompt_path = prompt_path
        self.schema_json = schema_json
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set (check .env)")
        self.client = openai.OpenAI(api_key=api_key)

        with open(prompt_path, "r") as f:
            self.prompt_template = f.read()
        
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        caen_file = os.path.join(project_root, "config", "caen.txt")
        self.caen_reference = ""
        if os.path.exists(caen_file):
            with open(caen_file, "r", encoding="utf-8") as f:
                self.caen_reference = f.read()

    def extract(self, text):
        prompt = self.prompt_template
        prompt = prompt.replace("{{schema}}", self.schema_json)
        prompt = prompt.replace("{{caen_reference}}", self.caen_reference)
        prompt = prompt + "\n\n" + text

        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        return json.loads(content)  # Parse JSON before returning
