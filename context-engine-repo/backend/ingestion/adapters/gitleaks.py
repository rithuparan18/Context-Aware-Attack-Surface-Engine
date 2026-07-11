import json
from typing import List, Dict, Any

def parse_gitleaks(file_path: str) -> List[Dict[str, Any]]:
    """
    Parses raw Gitleaks JSON output and converts it into standard RawEntity dictionaries.
    """
    raw_entities = []
    
    try:
        with open(file_path, 'r') as f:
            gitleaks_data = json.load(f)
            
        for finding in gitleaks_data:
            # We construct a clean RawEntity that Member 4's normalizer can easily map 
            # to the strict contract.json Node schema.
            raw_entity = {
                "source_tool": "gitleaks",
                "entity_type": "credential",
                "raw_value": finding.get("Secret", ""),
                "metadata": {
                    "rule_id": finding.get("RuleID", "unknown"),
                    "file_found_in": finding.get("File", "unknown"),
                    "author": finding.get("Author", "unknown"),
                    "commit": finding.get("Commit", "unknown")
                }
            }
            raw_entities.append(raw_entity)
            
    except FileNotFoundError:
        print(f"[!] Error: Could not find mock file at {file_path}")
    except json.JSONDecodeError:
        print(f"[!] Error: {file_path} is not valid JSON")
        
    return raw_entities

# Quick standalone test for Day 1 isolation verification
if __name__ == "__main__":
    mock_path = "../../mock_data/raw_gitleaks.json"
    results = parse_gitleaks(mock_path)
    print(json.dumps(results, indent=2))
