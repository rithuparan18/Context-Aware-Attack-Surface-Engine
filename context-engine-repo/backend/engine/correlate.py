from .graph_store import get_graph

def run_correlation_engine(raw_data_list):
    """
    Pod 2: Entity Resolution and Relationship Edge Building.
    Deduplicates incoming network data and connects vulnerable vectors.
    """
    graph = get_graph()
    
    print("\n=== RUNNING CORRELATION ENGINE ===")
    
    # 1. DEDUPLICATION (Entity Resolution)
    unique_nodes = {}
    for item in raw_data_list:
        label = item.get("label")
        if not label:
            continue
        if label not in unique_nodes:
            unique_nodes[label] = item
        else:
            print(f"[Deduplication] Merging duplicate asset data: {label}")

    # 2. POPULATE CLEAN ENGINE NODES
    for label, node_data in unique_nodes.items():
        graph.add_node(label, type=node_data.get("type"))

    # 3. EDGE CORRELATION (The Matchmaker Logic)
    all_nodes = list(unique_nodes.values())
    for item in all_nodes:
        if item.get("type") == "credential":
            attributes = item.get("attributes", {})
            target_domain = attributes.get("associated_domain")
            
            if target_domain and target_domain in unique_nodes:
                graph.add_edge(item["label"], target_domain, relation="EXPLOITS")
                print(f"[Match Found!] Linked {item['label']} -> {target_domain}")

    print("\n=== CORRELATION ENGINE PROCESSING COMPLETE ===")
    print(f"Total Unique Graph Nodes Stored: {graph.number_of_nodes()}")
    print(f"Total Active Correlation Edges: {graph.number_of_edges()}")
    print("==============================================\n")
    
    return graph