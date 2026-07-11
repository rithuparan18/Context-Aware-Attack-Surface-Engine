import hashlib
from .graph_store import get_graph

def run_correlation_engine(raw_data_list):
    """
    Pod 2: Entity Resolution and Relationship Edge Building.
    Deduplicates incoming network data and connects vulnerable vectors.
    """
    graph = get_graph()
    
    print("\n=== RUNNING CORRELATION ENGINE ===")
    
    # 1. DEDUPLICATION (Entity Resolution)
    # Using 'id' instead of 'label' to strictly match the Pydantic schema contract
    unique_nodes = {}
    for item in raw_data_list:
        node_id = item.get("id")
        if not node_id:
            continue
        if node_id not in unique_nodes:
            unique_nodes[node_id] = item
        else:
            print(f"[Deduplication] Merging duplicate asset data: {node_id}")

    # 2. POPULATE CLEAN ENGINE NODES
    # Unpack the entire node dictionary (**node_data) to preserve attributes and ROI placeholders
    for node_id, node_data in unique_nodes.items():
        graph.add_node(node_id, **node_data)

    # 3. EDGE CORRELATION (The Matchmaker Logic)
    all_nodes = list(unique_nodes.values())
    for item in all_nodes:
        if item.get("type") == "credential":
            attributes = item.get("attributes", {})
            target_domain_id = attributes.get("associated_domain")
            
            # Ensure the target actually exists in our deduplicated pool
            if target_domain_id and target_domain_id in unique_nodes:
                
                # Generate a strict, deterministic ID for the edge
                edge_id_string = f"{item['id']}_{target_domain_id}_grants_access_to"
                edge_id = hashlib.md5(edge_id_string.encode()).hexdigest()
                
                # Add the edge using strictly allowed relationships and confidence scores
                graph.add_edge(
                    item["id"], 
                    target_domain_id, 
                    id=edge_id, 
                    relationship="grants_access_to", 
                    confidence=0.85
                )
                print(f"[Match Found!] Linked {item['id']} -> {target_domain_id}")

    print("\n=== CORRELATION ENGINE PROCESSING COMPLETE ===")
    print(f"Total Unique Graph Nodes Stored: {graph.number_of_nodes()}")
    print(f"Total Active Correlation Edges: {graph.number_of_edges()}")
    print("==============================================\n")
    
    return graph
