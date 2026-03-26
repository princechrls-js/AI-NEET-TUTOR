import os
import json
from typing import Dict, Any

def save_metadata(subject: str, filename: str, data: Dict[str, Any]):
    """
    Saves metadata side-by-side with chunk extractions for traceability.
    """
    base_path = os.path.join("app", "data", "processed", subject)
    os.makedirs(base_path, exist_ok=True)
    
    file_path = os.path.join(base_path, f"{filename}_metadata.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def dict_to_string(metadata: Dict[str, Any]) -> str:
    """
    Convert dictionary metadata into a formatted string for injection.
    """
    return ", ".join([f"{k}: {v}" for k, v in metadata.items() if v])
