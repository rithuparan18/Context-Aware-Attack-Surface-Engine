import networkx as nx
import json
from typing import Dict, Any, List

# Re-defining Node for standalone execution (Matches Pod 1)
class Node:
    def __init__(self, node_id: str, node_type: str, label: str, source_tool: str, attributes: Dict[str, Any]):
        self.id = node_id
        self.type = node_type
        self.label = label
        self.source_tool = source_tool
        self.attributes = attributes

class CorrelationEngine:
    def __init__(self):
        # SREENIVAS: Task 1 (Initialize the State Manager)
        # Using a MultiDiGraph to allow multiple different relationship paths between two assets
        self.graph = nx.MultiDiGraph()

    # ==========================================
    # KOWSHIK: Task 1 & 2 (Entity Resolver)
    # ==========================================
    def ingest_node(self, new_node: Node):
        """Processes incoming nodes from Pod 1 with strict deduplication and merging."""
        
        if self.graph.has_node(new_node.id):
            # Conflict Resolution: Merge attributes instead of overwriting
            existing = self.graph.nodes[new_node.id]
            
            for key, val in new_node.attributes.items():
                if isinstance(val, list) and key in existing.get('attributes', {}):
                    # Deduplicate lists (e.g., merging new open ports with existing ones)
                    merged_list = list(set(existing['attributes'][key] + val))
                    existing['attributes'][key] = merged_list
                else:
                    # Overwrite scalars with the newest data
                    existing['attributes'][key] = val
                    
            print(f"[~] RESOLVED: Merged attributes into existing node -> {new_node.label}")
        else:
            # Add fresh node and immediately check for new edges
            self.graph.add_node(new_node.id, **new_node.__dict__)
            print(f"[+] ADDED: New node mapped -> {new_node.label}")
            
        # Trigger Navya's logic to see if this node connects to anything else
        self._evaluate_edges_for_node(new_node.id)

    # ==========================================
    # NAVYA: Task 1 & 2 (The Edge Builder)
    # ==========================================
    def _evaluate_edges_for_node(self, source_id: str):
        """Declarative rules engine. Optimized to only check the newly ingested node."""
        source_data = self.graph.nodes[source_id]
        
        for target_id, target_data in self.graph.nodes(data=True):
            if source_id == target_id:
                continue

            # RULE 1: Credentials grant access to Domains/Services
            if source_data['type'] == 'credential' and target_data['type'] in ['domain', 'ip', 'service']:
                # Example Logic: If the credential file belongs to the domain
                if "aws" in source_data['label'].lower() or "git" in source_data['label'].lower():
                    self._add_edge(source_id, target_id, "grants_access_to", confidence=0.85)

            # RULE 2: IPs query Domains (Subdomain resolution)
            if source_data['type'] == 'domain' and target_data['type'] == 'ip':
                self._add_edge(source_id, target_id, "resolves_to", confidence=1.0)
                
            # RULE 3: Vulnerabilities compromise Services
            if source_data['type'] == 'vulnerability' and target_data['type'] in ['service', 'domain']:
                self._add_edge(source_id, target_id, "compromises", confidence=0.95)

    def _add_edge(self, source: str, target: str, relationship: str, confidence: float):
        """Implements confidence thresholding before committing the edge."""
        # Threshold restriction (Must be > 0.75)
        if confidence > 0.75:
            # Prevent duplicate edges of the same relationship
            existing_edges = self.graph.get_edge_data(source, target)
            if existing_edges:
                for edge_val in existing_edges.values():
                    if edge_val.get('relationship') == relationship:
                        return # Edge already exists
            
            self.graph.add_edge(source, target, relationship=relationship, confidence=confidence)
            print(f"[>] EDGE: {source} --[{relationship}]--> {target}")

    # ==========================================
    # SREENIVAS: Task 2 (The Exporter)
    # ==========================================
    def export_to_frontend_schema(self) -> Dict[str, Any]:
        """Translates the complex NetworkX object into the clean JSON React expects."""
        payload = {"nodes": [], "links": []}
        
        # Format Nodes
        for node_id, data in self.graph.nodes(data=True):
            clean_node = {k: v for k, v in data.items() if k != "id"} # Avoid duplicate ID keys
            clean_node["id"] = str(node_id)
            payload["nodes"].append(clean_node)
            
        # Format Links
        for u, v, data in self.graph.edges(data=True):
            payload["links"].append({
                "source": str(u),
                "target": str(v),
                "relationship": data.get("relationship", "unknown"),
                "confidence": data.get("confidence", 1.0)
            })
            
        return payload

# ==========================================
# TEST RUNNER (Proving the Pipeline)
# ==========================================
if __name__ == "__main__":
    engine = CorrelationEngine()
    
    # Simulating Pod 1 Queue output
    mock_ingestion = [
        Node("ip_10.0.0.1", "ip", "10.0.0.1", "nmap", {"ports": [80, 443]}),
        Node("dom_bank.com", "domain", "bank.com", "amass", {}),
        Node("cred_aws", "credential", "AWS_ACCESS_KEY", "gitleaks", {"file": "prod.yml"}),
        # Simulating Kowshik's deduplication rule (an updated Nmap scan for the same IP)
        Node("ip_10.0.0.1", "ip", "10.0.0.1", "nmap", {"ports": [8080], "os": "Linux"})
    ]
    
    print("--- IGNITING POD 2 ENGINE ---")
    for node in mock_ingestion:
        engine.ingest_node(node)
        
    print("\n--- FINAL FRONTEND PAYLOAD ---")
    print(json.dumps(engine.export_to_frontend_schema(), indent=2))