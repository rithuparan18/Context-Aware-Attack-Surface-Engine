from typing import List, Dict, Any

def resolve_entities(raw_nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicates a list of raw nodes based on deterministic match rules.
    Merge condition: Exact match on the 'label' field (which holds IP, Domain, or Credential string).
    """
    merged_nodes = {}

    for node in raw_nodes:
        # Our deterministic matching key is the label (e.g., 'jenkins.acme-corp.example' or '192.168.1.1')
        match_key = node.get("label")

        # Fallback: If a node somehow lacks a label, keep it isolated by its ID to prevent crashing
        if not match_key:
            merged_nodes[node.get("id")] = node
            continue

        if match_key in merged_nodes:
            # --- MERGE CONFLICT RESOLUTION ---
            existing = merged_nodes[match_key]

            # 1. Concatenate source tools (Crucial for the GD: proves we correlated multiple data sources)
            if node.get("source_tool") not in existing.get("source_tool", ""):
                existing["source_tool"] = f"{existing['source_tool']}, {node['source_tool']}"

            # 2. Merge attributes (Assume the highest risk scenario if sources conflict)
            e_attrs = existing.get("attributes", {})
            n_attrs = node.get("attributes", {})

            existing["attributes"] = {
                # If ANY source says it is internet facing, we treat it as internet facing
                "internet_facing": e_attrs.get("internet_facing", False) or n_attrs.get("internet_facing", False),
                
                # If ANY source found an exploit, it is flagged
                "has_public_exploit": e_attrs.get("has_public_exploit", False) or n_attrs.get("has_public_exploit", False),
                
                # If ANY source detected a WAF, log it
                "behind_waf": e_attrs.get("behind_waf", False) or n_attrs.get("behind_waf", False),
                
                # Take the highest confidence score between the two sources
                "confidence": max(e_attrs.get("confidence", 0.0), n_attrs.get("confidence", 0.0))
            }
            
            # NOTE: We do not touch 'roi_score' or 'is_chokepoint' here. Pod 3 handles that.
        else:
            # First time seeing this exact entity label, add it to our tracking dictionary
            merged_nodes[match_key] = node

    # Return the deduplicated list of Node dictionaries, ready for Member 6 to build edges
    return list(merged_nodes.values())

# --- DAY 1 LOCAL TESTING FIXTURE ---
if __name__ == "__main__":
    # Mock data directly reflecting the contract.json structure
    pod_1_mock_output = [
        {
            "id": "node-001",
            "type": "service",
            "label": "jenkins.acme-corp.example",
            "source_tool": "nmap",
            "attributes": {"internet_facing": True, "has_public_exploit": False, "confidence": 0.9}
        },
        {
            "id": "node-002",
            "type": "subdomain",
            "label": "jenkins.acme-corp.example",
            "source_tool": "amass",
            "attributes": {"internet_facing": False, "has_public_exploit": False, "confidence": 0.95}
        }
    ]
    
    clean_nodes = resolve_entities(pod_1_mock_output)
    print(f"Original Nodes: {len(pod_1_mock_output)} | Deduplicated Nodes: {len(clean_nodes)}")
    print(f"Merged Node Details: {clean_nodes[0]}")
