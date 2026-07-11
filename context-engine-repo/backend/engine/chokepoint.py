import networkx as nx

def find_chokepoints(nodes: list, edges: list, top_n: int = 1) -> dict:
    """
    Parses flat node and edge lists, computes betweenness centrality using NetworkX,
    flags the top structural chokepoint node, and builds the payload summary.
    """
    if not nodes:
        return {"nodes": [], "edges": edges, "chokepoint_summary": {}}

    # 1. Initialize NetworkX Directed Graph
    G = nx.DiGraph()
    
    # Load nodes into graph memory
    for node in nodes:
        G.add_node(node["id"], **node)
        
    # Load edges into graph memory
    for edge in edges:
        G.add_edge(edge["source"], edge["target"])
        
    # 2. Compute Betweenness Centrality
    # Measures how frequently a node falls on the shortest path between all other node pairs
    centrality = nx.betweenness_centrality(G)
    
    if not centrality:
        return {"nodes": nodes, "edges": edges, "chokepoint_summary": {}}

    # Sort nodes by highest centrality score
    ranked_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
    
    # 3. Flag the Top Chokepoints and Clean states
    top_node_id = ranked_nodes[0][0]
    
    updated_nodes = []
    for node in nodes:
        node_copy = node.copy()
        if node_copy["id"] == top_node_id:
            node_copy["is_chokepoint"] = True
            node_copy["chokepoint_rank"] = 1
        else:
            node_copy["is_chokepoint"] = False
            node_copy["chokepoint_rank"] = None
        updated_nodes.append(node_copy)

    # 4. Synthesize the Chokepoint Summary Payload (Matching the exact contract schema)
    chokepoint_summary = {
        "top_node_id": top_node_id,
        "attack_paths_severed": 6,  # Mock metrics required for Day 1 visualization
        "total_attack_paths": 9,
        "coverage_pct": 66.7
    }

    return {
        "nodes": updated_nodes,
        "edges": edges,
        "chokepoint_summary": chokepoint_summary
    }
