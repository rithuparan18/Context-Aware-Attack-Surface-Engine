# NOT WIRED INTO THE LIVE PIPELINE.
# Real Gitleaks JSON parser (reads a gitleaks report from disk).
#
# ingestion.py (in the parent dir) is the file actually on the request
# path — it owns Layer 1 end-to-end and emits GraphEngine's schema
# directly, mocked data included, so nothing here is currently called
# by api/server.py.
#
# This is the v2 path from the architecture doc's Section 5
# ('Live scanning...the Evasion Config becomes an active middleware
# around real HTTP adapters'): once you want ingestion.py's mocked
# nmap/amass/gitleaks calls replaced with real tool output read from
# disk, this is where that logic lives. Wire it in by having
# InfrastructureRecon / SecretsRecon in ingestion.py call these
# parsers on real tool output instead of returning the mocked lists,
# then map their RawEntity shape onto GraphEngine's node schema
# (id/type/label/source_tool/attributes) at the call site.

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
