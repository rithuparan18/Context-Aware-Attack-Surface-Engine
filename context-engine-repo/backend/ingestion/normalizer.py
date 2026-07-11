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