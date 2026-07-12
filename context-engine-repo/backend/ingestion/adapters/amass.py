# NOT WIRED INTO THE LIVE PIPELINE.
# Real Amass output parser (reads a passive-enum text file from disk).
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
