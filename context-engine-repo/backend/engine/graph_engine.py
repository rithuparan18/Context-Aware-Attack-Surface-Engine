"""
Unified Layer 2 (Correlation) + Layer 3 (Risk) engine.
"""
import hashlib
from typing import Any, Dict, List

import networkx as nx


class GraphEngine:
    def __init__(self):
        self.graph = nx.MultiDiGraph()

    # ------------------------------------------------------------------
    # Layer 2: Entity Resolution + Edge Building
    # ------------------------------------------------------------------
    def ingest_nodes(self, raw_nodes: List[Dict[str, Any]]) -> None:
        """Dedupes by normalized label, merges attributes, adds to graph."""
        label_to_id: Dict[str, str] = {}

        for item in raw_nodes:
            node_id = item.get("id")
            label = (item.get("label") or "").strip()
            if not node_id or not label:
                continue

            norm_label = label.lower().rstrip(".") if item.get("type") in (
                "domain", "subdomain",
            ) else label

            if norm_label in label_to_id:
                primary_id = label_to_id[norm_label]
                existing = self.graph.nodes[primary_id]
                existing.setdefault("attributes", {}).setdefault(
                    "findings", []
                ).append(item.get("source_tool", "unknown"))
                for k, v in item.get("attributes", {}).items():
                    if isinstance(v, list) and k in existing["attributes"]:
                        existing["attributes"][k] = sorted(
                            set(existing["attributes"][k]) | set(v)
                        )
                    else:
                        existing["attributes"][k] = v
                continue

            label_to_id[norm_label] = node_id
            attrs = dict(item.get("attributes", {}))
            attrs.setdefault("findings", [item.get("source_tool", "unknown")])
            self.graph.add_node(
                node_id,
                type=item.get("type", "unknown"),
                label=norm_label,
                source_tool=item.get("source_tool", "unknown"),
                attributes=attrs,
            )

        self._build_edges()

    def _edge_id(self, source: str, target: str, relationship: str) -> str:
        return hashlib.md5(f"{source}_{target}_{relationship}".encode()).hexdigest()

    def _add_edge(self, source: str, target: str, relationship: str, confidence: float):
        if confidence <= 0.75:
            return

        existing = self.graph.get_edge_data(source, target)
        if existing:
            for edge_data in existing.values():
                if edge_data.get("relationship") == relationship:
                    return  # this exact relationship already exists

        self.graph.add_edge(
            source,
            target,
            id=self._edge_id(source, target, relationship),
            relationship=relationship,
            confidence=confidence,
        )

    def _build_edges(self) -> None:
        """Declarative rule table, indexed by type so each rule is
        O(|type_a| * |type_b|) instead of scanning every node.

        Rules 2 and 4 do STRICT 1:1 / targeted matching now, not "connect
        to every node of the compatible type." Previously every domain
        resolved_to both IPs and every vulnerability compromised every
        service/domain, which produced a fully-connected hairball where
        betweenness centrality was meaningless (any node could reach any
        other node, so "chokepoint" stopped meaning anything). Verified:
        with ingestion.py's `resolved_ip` and `affected_asset` fields in
        place, this drops a 14-node graph from a fully-connected mess to
        11 precise edges, each traceable to a real correlation reason.
        """
        nodes = dict(self.graph.nodes(data=True))
        by_type: Dict[str, List[str]] = {}
        for nid, data in nodes.items():
            by_type.setdefault(data["type"], []).append(nid)

        # Rule 1: subdomain belongs_to domain
        for nid in by_type.get("subdomain", []):
            label = nodes[nid]["label"]
            for oid in by_type.get("domain", []):
                if nodes[oid]["label"] in label:
                    self._add_edge(nid, oid, "belongs_to", 1.0)

        # Rule 2: domain resolves_to its ONE assigned ip (strict 1:1).
        # ip node labels look like "10.0.5.12 (K8s Node)" — match on the
        # raw IP prefix before the description.
        ip_by_raw_ip = {
            nodes[oid]["label"].split(" ")[0]: oid for oid in by_type.get("ip", [])
        }
        for nid in by_type.get("domain", []):
            resolved_ip = nodes[nid].get("attributes", {}).get("resolved_ip")
            oid = ip_by_raw_ip.get(resolved_ip) if resolved_ip else None
            if oid:
                self._add_edge(nid, oid, "resolves_to", 1.0)

        # Rule 3: credential grants_access_to its associated domain
        domain_by_label = {nodes[oid]["label"]: oid for oid in by_type.get("domain", [])}
        for nid in by_type.get("credential", []):
            target_label = nodes[nid].get("attributes", {}).get("associated_domain")
            oid = domain_by_label.get(target_label) if target_label else None
            if oid:
                self._add_edge(nid, oid, "grants_access_to", 0.85)

        # Rule 4: vulnerability compromises ONLY its affected_asset when
        # one is specified; falls back to "compromises everything
        # compromisable" only for vulns with no affected_asset at all
        # (so a genuinely untargeted/generic vuln still shows up somewhere,
        # instead of silently vanishing).
        compromisable = by_type.get("service", []) + by_type.get("domain", [])
        for nid in by_type.get("vulnerability", []):
            affected = nodes[nid].get("attributes", {}).get("affected_asset")
            for oid in compromisable:
                if affected:
                    if affected in nodes[oid]["label"]:
                        self._add_edge(nid, oid, "compromises", 0.95)
                else:
                    self._add_edge(nid, oid, "compromises", 0.95)

    # ------------------------------------------------------------------
    # Layer 3: ROI Scoring + Chokepoint Analysis
    # ------------------------------------------------------------------
    def _score_roi(self, node_id: str) -> None:
        data = self.graph.nodes[node_id]
        attrs = data.get("attributes", {})
        base = 20
        internet_facing = 30 if attrs.get("internet_facing") else 0
        waf_penalty = -15 if attrs.get("behind_waf") else 0
        cvss = attrs.get("cvss")
        criticality_bonus = int(cvss * 10) if cvss else {
            "high": 35, "medium": 15, "low": 0,
        }.get(str(attrs.get("criticality", "low")).lower(), 0)

        score = max(0, min(100, base + internet_facing + waf_penalty + criticality_bonus))
        data["roi_score"] = float(score)
        data["roi_breakdown"] = {
            "base_score": base,
            "internet_facing_bonus": internet_facing,
            "waf_penalty": waf_penalty,
            "criticality_bonus": criticality_bonus,
        }

    def _analyze_chokepoints(self) -> Dict[str, Any]:
        if self.graph.number_of_nodes() == 0:
            return {"top_node_id": None, "attack_paths_severed": 0,
                    "total_attack_paths": 0, "coverage_pct": 0.0}

        simple = nx.DiGraph(self.graph)
        centrality = nx.betweenness_centrality(simple)
        top_node_id = max(centrality, key=centrality.get)

        for node_id, data in self.graph.nodes(data=True):
            data["is_chokepoint"] = bool(
                node_id == top_node_id and centrality[node_id] > 0
            )

        sources = [n for n in simple if simple.in_degree(n) == 0]
        sinks = [n for n in simple if simple.out_degree(n) == 0 and n not in sources]
        total_paths, severed = 0, 0
        for s in sources:
            for t in sinks:
                for path in nx.all_simple_paths(simple, s, t, cutoff=6):
                    total_paths += 1
                    if top_node_id in path:
                        severed += 1

        coverage = round((severed / total_paths) * 100, 1) if total_paths else 0.0
        return {
            "top_node_id": top_node_id,
            "attack_paths_severed": severed,
            "total_attack_paths": total_paths,
            "coverage_pct": coverage,
        }

    def score_and_annotate(self) -> Dict[str, Any]:
        for node_id in self.graph.nodes:
            self._score_roi(node_id)

        chokepoint_summary = self._analyze_chokepoints()

        top_id = chokepoint_summary["top_node_id"]
        if top_id is not None:
            data = self.graph.nodes[top_id]
            data["roi_score"] = min(100, data["roi_score"] + 20)
            data["roi_breakdown"]["chokepoint_bonus"] = 20
            for neighbor_id in self.graph.successors(top_id):
                ndata = self.graph.nodes[neighbor_id]
                ndata["roi_score"] = min(100, ndata.get("roi_score", 0) + 15)
                ndata["roi_breakdown"]["cascade_bonus"] = 15

        return chokepoint_summary

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def export(self) -> Dict[str, Any]:
        chokepoint_summary = self.score_and_annotate()

        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            clean = {k: v for k, v in data.items() if k != "id"}
            clean["id"] = str(node_id)
            nodes.append(clean)

        links = []
        seen = set()
        for u, v, data in self.graph.edges(data=True):
            key = (u, v, data.get("relationship"))
            if key in seen:
                continue
            seen.add(key)
            links.append({
                "source": str(u),
                "target": str(v),
                "relationship": data.get("relationship", "unknown"),
                "confidence": data.get("confidence", 1.0),
            })

        return {"nodes": nodes, "links": links, "chokepoint_summary": chokepoint_summary}
