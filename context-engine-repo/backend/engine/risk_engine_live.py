import networkx as nx
from typing import Dict, Any

class RiskEngineLive:
    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph

    def _analyze_chokepoints(self):
        """Finds the central node that connects the most attack paths."""
        if len(self.graph.nodes) == 0:
            return

        # Betweenness centrality requires a standard DiGraph
        di_graph = nx.DiGraph(self.graph)
        centrality_scores = nx.betweenness_centrality(di_graph)

        if not centrality_scores:
            return

        # Identify the absolute highest risk chokepoint
        chokepoint_id = max(centrality_scores, key=centrality_scores.get)
        
        for node_id, data in self.graph.nodes(data=True):
            # Flag it for the React UI to apply the glowing red border
            data['is_chokepoint'] = (node_id == chokepoint_id and centrality_scores[node_id] > 0)

    def _calculate_roi_and_cascade(self):
        """Calculates base ROI and cascades critical risk to adjacent nodes."""
        
        # Pass 1: Base Scoring & CVSS Injection
        for node_id, data in self.graph.nodes(data=True):
            base_score = 20
            criticality = 0
            
            # Inject dynamic CVSS modifiers if it's a vulnerability
            if data.get('type') == 'vulnerability':
                cvss = data.get('attributes', {}).get('cvss', 5.0)
                criticality = int(cvss * 10)  # E.g., CVSS 9.8 adds 98 points
                
            waf_penalty = -15 if 'waf' in data.get('attributes', {}) else 0

            data['roi_breakdown'] = {
                "base_score": base_score,
                "criticality": criticality,
                "waf_penalty": waf_penalty
            }
            data['roi_score'] = min(100, max(0, base_score + criticality + waf_penalty))

        # Pass 2: The Cascade Effect (Chokepoints infect neighbors)
        for node_id, data in self.graph.nodes(data=True):
            if data.get('is_chokepoint'):
                data['roi_score'] = min(100, data['roi_score'] + 20)
                data['roi_breakdown']['chokepoint_bonus'] = 20
                
                # Cascade risk forward
                for neighbor_id in self.graph.successors(node_id):
                    neighbor = self.graph.nodes[neighbor_id]
                    neighbor['roi_score'] = min(100, neighbor.get('roi_score', 0) + 15)
                    neighbor['roi_breakdown']['cascade_bonus'] = 15

    def execute(self) -> nx.MultiDiGraph:
        """Executes the full risk suite and returns the annotated graph."""
        self._analyze_chokepoints()
        self._calculate_roi_and_cascade()
        return self.graph