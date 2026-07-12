# NOT WIRED INTO THE LIVE PIPELINE.
# Mock RawEntity generator used before schema unification.
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

import uuid

def run_all_parsers() -> list[dict]:
    """
    Pod 1 Master Engine: Ingests raw tool outputs and normalizes them 
    into strict dictionaries that match the Node Pydantic schema.
    """
    print("[Pod 1] Executing Nmap, Amass, and Gitleaks parsers...")
    
    raw_nodes = []

    # 1. Mocking Ajay's Nmap Output
    raw_nodes.append({
        "id": f"node_{uuid.uuid4().hex[:8]}",
        "type": "ip",
        "label": "192.168.1.100",
        "source_tool": "nmap",
        "attributes": {"open_ports": [80, 443, 8080]}
    })

    # 2. Mocking Ajay's Amass Output (With weird capitalization to test Koushik's resolver)
    raw_nodes.append({
        "id": f"node_{uuid.uuid4().hex[:8]}",
        "type": "domain",
        "label": "http://Staging.Bank.com:8080",
        "source_tool": "amass",
        "attributes": {"resolved_ip": "192.168.1.100"}
    })

    # 3. Mocking Santosh's Gitleaks Output
    raw_nodes.append({
        "id": f"node_{uuid.uuid4().hex[:8]}",
        "type": "credential",
        "label": "aws-access-token",
        "source_tool": "gitleaks",
        "attributes": {
            "email": "bot@acme-corp.example", 
            "file": "config/production.yml",
            "associated_domain": "staging.bank.com" # This will trigger Navya's correlation edge!
        }
    })

    return raw_nodes