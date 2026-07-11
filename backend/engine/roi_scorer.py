# backend/engine/roi_scorer.py

def calculate_roi(node: dict) -> dict:
    """
    Takes a single node dictionary, calculates the Attacker ROI score (0-100),
    and adds the final score and math breakdown directly back to the node.
    """
    # 1. Start with the base score (Task 1)
    base_score = 20
    
    # Safely get the inner attributes dictionary
    attributes = node.get("attributes", {})
    
    # Track the point adjustments
    internet_facing_mod = 0
    waf_penalty = 0
    criticality_mod = 0
    
    # 2. Check if the asset is internet facing (+30) (Task 1)
    if attributes.get("internet_facing") is True:
        internet_facing_mod = 30
        
    # 3. Check if the asset is behind a firewall (-15) (Task 2)
    if attributes.get("behind_waf") is True:
        waf_penalty = -15
        
    # 4. Check Business Criticality Impact (Task 3)
    criticality = attributes.get("criticality", "low").lower()
    if criticality == "high":
        criticality_mod = 35
    elif criticality == "medium":
        criticality_mod = 15
    else:
        criticality_mod = 0
        
    # 5. Calculate total score
    total_score = base_score + internet_facing_mod + waf_penalty + criticality_mod
    
    # Ensure score stays within logical bounds (0 to 100)
    if total_score < 0:
        total_score = 0
    if total_score > 100:
        total_score = 100
        
    # 6. Write the final integer back to the node schema (Task 2/3 Requirement)
    node["roi_score"] = total_score
    
    # 7. Save the exact math breakdown ("receipt") to the node (Task 2/3 Requirement)
    node["roi_factors"] = {
        "base_score": base_score,
        "internet_facing_bonus": internet_facing_mod,
        "waf_penalty": waf_penalty,
        "criticality_bonus": criticality_mod
    }
    
    return node


# ==========================================
# DAY 1 SANDBOX TESTING AREA
# ==========================================
if __name__ == "__main__":
    print("--- Running Test 3: Critical Database Server (Internet Facing, WAF Protected, High Criticality) ---")
    test_node_3 = {
        "id": "node-103",
        "type": "database",
        "attributes": {
            "internet_facing": True,
            "behind_waf": True,
            "criticality": "high"
        }
    }
    # Math: 20 (base) + 30 (internet) - 15 (waf) + 35 (high criticality) = 70
    result_3 = calculate_roi(test_node_3)
    print(f"Calculated Score: {result_3['roi_score']} (Expected: 70)")
    print(f"Receipt Breakdown: {result_3['roi_factors']}")
    print("-" * 50)