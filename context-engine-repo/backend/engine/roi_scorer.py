import networkx as nx

def calculate_roi(node: dict) -> dict:
    """
    Takes a single node dictionary, calculates the Attacker ROI score (0-100),
    and adds the final score and math breakdown directly back to the node.
    """
    base_score = 20
    attributes = node.get("attributes", {})
    
    internet_facing_mod = 0
    waf_penalty = 0
    criticality_mod = 0
    
    if attributes.get("internet_facing") is True:
        internet_facing_mod = 30
        
    if attributes.get("behind_waf") is True:
        waf_penalty = -15
        
    criticality = attributes.get("criticality", "low").lower()
    if criticality == "high":
        criticality_mod = 35
    elif criticality == "medium":
        criticality_mod = 15
    else:
        criticality_mod = 0
        
    total_score = base_score + internet_facing_mod + waf_penalty + criticality_mod
    
    if total_score < 0:
        total_score = 0
    if total_score > 100:
        total_score = 100
        
    node["roi_score"] = float(total_score)
    
    # Pod 3 called this 'roi_factors', but Pydantic needs 'roi_breakdown'
    node["roi_breakdown"] = {
        "base_score": base_score,
        "internet_facing_bonus": internet_facing_mod,
        "waf_penalty": waf_penalty,
        "criticality_bonus": criticality_mod
    }
    
    return node

def score_graph(graph: nx.DiGraph):
    """
    The Master Wrapper: Iterates through Pod 2's NetworkX graph, extracts the raw node 
    data, passes it to Pod 3's calculate_roi engine, and stamps the score back on the graph.
    """
    for node_id, node_data in graph.nodes(data=True):
        # Run Pod 3's math engine on the node
        updated_node = calculate_roi(node_data)
        
        # Stamp the newly calculated metrics back onto the NetworkX graph attributes
        graph.nodes[node_id]["roi_score"] = updated_node["roi_score"]
        graph.nodes[node_id]["roi_breakdown"] = updated_node["roi_breakdown"]
        
    return graph