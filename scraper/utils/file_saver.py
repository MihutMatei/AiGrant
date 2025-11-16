import os
import json
import uuid

def save_json(output_dir, data_list):
    os.makedirs(output_dir, exist_ok=True)

    if isinstance(data_list, dict):
        data_list = [data_list]

    for item in data_list:
        filename = f"{uuid.uuid4()}.json"
        path = os.path.join(output_dir, filename)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(item, f, indent=2, ensure_ascii=False)

        print(f"[SAVED] {path}")
