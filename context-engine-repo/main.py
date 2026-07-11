import json
import networkx as nx
from networkx.readwrite import json_graph
from backend.ingestion.normalizer import run_all_parsers
from backend.engine.correlate import run_correlation_engine
from backend.engine.roi_scorer import score_graph

def execute_full_attack_surface_scan():
    print("🚀 INITIATING CONTEXT-AWARE ATTACK SURFACE ENGINE...")
    
    # --- PHASE 1: INGESTION (Pod 1) ---
    print("\n[+] Phase 1: Ingesting recon data...")
    raw_data = run_all_parsers()
    
    # --- PHASE 2: CORRELATION & ATTACK GRAPH (Pod 2) ---
    print("\n[+] Phase 2: Building Attack Graph...")
    graph = run_correlation_engine(raw_data)
    
    # --- PHASE 3: ADVERSARY ROI MATH (Pod 3) ---
    print("\n[+] Phase 3: Calculating Attacker ROI...")
    scored_graph = score_graph(graph)
    
    # --- PHASE 4: UI HANDOFF (Pod 4) ---
    print("\n[+] Phase 4: Exporting JSON for Frontend...")
    
    # Convert the NetworkX graph into a serialized dictionary
    graph_data = json_graph.node_link_data(scored_graph)
    
    # Dump the dictionary to a static JSON file
    with open("final_attack_graph.json", "w") as f:
        json.dump(graph_data, f, indent=4)
        
    print("\n✅ Enterprise Engine Execution Complete.")
    print(f"Total Nodes: {scored_graph.number_of_nodes()} | Total Edges: {scored_graph.number_of_edges()}")
    print("📁 Graph successfully exported to: final_attack_graph.json")

if __name__ == "__main__":
    execute_full_attack_surface_scan()