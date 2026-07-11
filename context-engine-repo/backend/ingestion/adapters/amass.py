import os

def parse_amass(file_path: str) -> list[dict]:
    if not os.path.exists(file_path):
        return []
        
    entities = []
    with open(file_path, "r") as f:
        for line in f:
            domain = line.strip()
            if domain:
                entities.append({
                    "type": "subdomain",
                    "extracted_value": domain,
                    "metadata": {
                        "discovery_method": "passive_scraping",
                        "confidence": 0.85
                    }
                })
    return entities
