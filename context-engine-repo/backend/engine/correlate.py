import hashlib
from urllib.parse import urlparse
from .graph_store import get_graph

def extract_clean_domain(label: str) -> str:
    """Koushik's Entity Resolver: Extracts a clean, normalized domain."""
    if not label:
        return ""
    
    label = label.strip()
    if "://" not in label:
        label = "https://" + label

    hostname = urlparse(label).hostname or ""
    return hostname.lower().rstrip(".")

def deduplicate_nodes(raw_data_list: list[dict]) -> dict:
    """
    Fuses Koushik's resolver with the Pydantic schema contract.
    Returns a dictionary of unique, validated nodes ready for NetworkX.
    """
    unique_nodes = {}
    label_to_id = {} # Maps the clean string to the primary Pydantic ID
    
    for item in raw_data_list:
        raw_label = item.get("label", "")
        node_id = item.get("id")
        
        # Apply normalization only to web assets
        clean_label = extract_clean_domain(raw_label) if item.get("type") in ["domain", "subdomain"] else raw_label
        
        if not clean_label or not node_id:
            continue
            
        if clean_label not in label_to_id:
            # First time seeing this asset
            item["label"] = clean_label
            if "attributes" not in item:
                item["attributes"] = {}
            item["attributes"]["findings"] = [item.get("source_tool", "unknown")]
            
            label_to_id[clean_label] = node_id
            unique_nodes[node_id] = item
        else:
            # We found a duplicate! Append its tool data to the master node
            primary_id = label_to_id[clean_label]
            print(f"[Resolver] Merging duplicate finding into: {clean_label}")
            unique_nodes[primary_id]["attributes"]["findings"].append(item.get("source_tool", "unknown"))

    return unique_nodes

def generate_edge_id(source: str, target: str, relationship: str) -> str:
    """Creates a deterministic, unique ID for every edge to prevent duplicates."""
    unique_string = f"{source}_{target}_{relationship}"
    return hashlib.md5(unique_string.encode()).hexdigest()

def run_correlation_engine(raw_data_list: list[dict]):
    """
    Pod 2 Master Engine: Deduplicates entities, loads them into NetworkX, 
    and mathematically correlates attack paths.
    """
    graph = get_graph()
    
    print("\n=== RUNNING CORRELATION ENGINE ===")
    
    # 1. DEDUPLICATION (Koushik's Logic)
    unique_nodes_dict = deduplicate_nodes(raw_data_list)

    # 2. POPULATE CLEAN ENGINE NODES
    for node_id, node_data in unique_nodes_dict.items():
        graph.add_node(node_id, **node_data)

    # 3. EDGE CORRELATION (Navya's Logic)
    all_nodes = list(unique_nodes_dict.values())
    
    domains = [n for n in all_nodes if n.get('type') == 'domain']
    subdomains = [n for n in all_nodes if n.get('type') == 'subdomain']
    credentials = [n for n in all_nodes if n.get('type') == 'credential']

    # Rule 1: Subdomain -> Domain (belongs_to)
    for sub in subdomains:
        for dom in domains:
            if dom['label'] in sub['label']:
                edge_id = generate_edge_id(sub['id'], dom['id'], "belongs_to")
                graph.add_edge(sub['id'], dom['id'], id=edge_id, relationship="belongs_to", confidence=1.0)

    # Rule 2: Credential -> Target Asset (grants_access_to) - HOTFIXED
    for cred in credentials:
        attributes = cred.get("attributes", {})
        target_domain_label = attributes.get("associated_domain")
        
        if target_domain_label:
            # Loop through the known domains to find the exact label match
            for dom in domains:
                if dom['label'] == target_domain_label:
                    edge_id = generate_edge_id(cred['id'], dom['id'], "grants_access_to")
                    graph.add_edge(cred['id'], dom['id'], id=edge_id, relationship="grants_access_to", confidence=0.85)
                    print(f"[Match Found!] Linked Credential {cred['id']} -> Asset {dom['id']}")

    print("\n=== CORRELATION ENGINE PROCESSING COMPLETE ===")
    print(f"Total Unique Graph Nodes Stored: {graph.number_of_nodes()}")
    print(f"Total Active Correlation Edges: {graph.number_of_edges()}")
    print("==============================================\n")
    
    return graph