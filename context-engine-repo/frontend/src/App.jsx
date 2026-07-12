import React, { useState, useCallback, useMemo, useRef } from "react";
import { ReactFlow, Controls, Background, applyNodeChanges, applyEdgeChanges } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import dagre from "dagre";

import DetailPanel from "./components/DetailPanel";

const getLayoutedElements = (nodes, edges, direction = 'LR') => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 180, height: 70 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  return {
    nodes: nodes.map((node) => {
      const nodeWithPosition = dagreGraph.node(node.id);
      return {
        ...node,
        position: { x: nodeWithPosition.x - 180 / 2, y: nodeWithPosition.y - 70 / 2 },
      };
    }),
    edges,
  };
};

function App() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showCriticalOnly, setShowCriticalOnly] = useState(false);

  const [targetInput, setTargetInput] = useState("");
  const [logs, setLogs] = useState(["[*] Context Engine C2 Console Initialized. Type a target and press ENGAGE PIPELINE."]);

  const runIdRef = useRef(0);

  const launchRecon = useCallback(async (target) => {
    const trimmedTarget = (target || "").trim();
    if (!trimmedTarget) {
      setLogs((prev) => [...prev, "[!] Enter a target domain first."]);
      return;
    }

    const thisRun = ++runIdRef.current;
    const isCurrentRun = () => runIdRef.current === thisRun;
    const logIfCurrent = (msg) => {
      if (isCurrentRun()) setLogs((prev) => [...prev, msg]);
    };

    setLoading(true);

    // BUGFIX: selectedNode was never cleared between runs. Switching targets
    // left the DetailPanel showing a node from the PREVIOUS graph — it looked
    // like "wrong" or "incomplete" data, but it was actually stale data from
    // a node that isn't even in the current graph anymore. Clear it up front
    // so the panel honestly reflects "nothing selected in this graph yet."
    setSelectedNode(null);

    logIfCurrent(`[*] Deploying orchestration layers against target: ${trimmedTarget}...`);

    const timers = [
      setTimeout(() => logIfCurrent("[+] [AMASS] Launching passive subdomain enumeration..."), 400),
      setTimeout(() => logIfCurrent("[+] [NMAP] Probing active host perimeters on ports 80, 443..."), 900),
      setTimeout(() => logIfCurrent("[+] [GITLEAKS] Scanning local repositories for leaked API secrets..."), 1400),
    ];

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/graph?target=${encodeURIComponent(trimmedTarget)}`
      );

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Backend returned ${response.status}`);
      }
      const data = await response.json();

      if (!isCurrentRun()) return;

      if (!data.nodes || data.nodes.length === 0) {
        logIfCurrent(`[!] No assets discovered for ${trimmedTarget}. Ingestion returned zero nodes.`);
        setNodes([]);
        setEdges([]);
        return;
      }

      const initialNodes = data.nodes.map((node) => ({
        id: String(node.id),
        data: { label: node.label || "Unknown Node", fullData: node },
        position: { x: 0, y: 0 },
        style: {
          background: (node.roi_score || 0) > 60 ? "#ef4444" : "#10b981",
          color: "#fff",
          borderRadius: "6px",
          padding: "10px",
          width: 170,
          textAlign: "center",
          border: node.is_chokepoint ? "3px solid #fbbf24" : "1px solid #374151",
          boxShadow: node.is_chokepoint ? "0 0 15px rgba(251, 191, 36, 0.5)" : "none",
        },
      }));

      const initialEdges = (data.links || []).map((link, index) => ({
        id: `e${index}-${link.source}-${link.target}`,
        source: String(link.source),
        target: String(link.target),
        animated: true,
        label: link.relationship,
        style: { stroke: "#9ca3af", strokeWidth: 2 },
      }));

      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(initialNodes, initialEdges);

      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
      logIfCurrent(`[+] [ENGINE] Ingestion complete. Graph successfully correlated for ${trimmedTarget}. (${initialNodes.length} nodes, ${initialEdges.length} edges)`);
    } catch (error) {
      logIfCurrent(`[!] PIPELINE ERROR: ${error.message}`);
    } finally {
      timers.forEach(clearTimeout);
      if (isCurrentRun()) setLoading(false);
    }
  }, []);

  // BUGFIX: previously a useEffect auto-ran launchRecon("bank.local") on
  // mount, so the app always showed a default graph before the user typed
  // anything. Removed — nothing loads until ENGAGE PIPELINE is clicked.

  const onNodesChange = useCallback((changes) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
  const onEdgesChange = useCallback((changes) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);

  const displayNodes = useMemo(() => !showCriticalOnly ? nodes : nodes.filter(n => n.data.fullData.roi_score > 60 || n.data.fullData.is_chokepoint), [nodes, showCriticalOnly]);
  const displayEdges = useMemo(() => {
    if (!showCriticalOnly) return edges;
    const visibleIds = new Set(displayNodes.map(n => n.id));
    return edges.filter(e => visibleIds.has(e.source) && visibleIds.has(e.target));
  }, [edges, displayNodes, showCriticalOnly]);

  return (
    <div style={{ display: "flex", flexDirection: "column", width: "100vw", height: "100vh", backgroundColor: "#0f172a", color: "#e2e8f0", fontFamily: "monospace" }}>

      <div style={{ display: "flex", alignItems: "center", gap: "15px", padding: "15px", backgroundColor: "#1e293b", borderBottom: "2px solid #334155" }}>
        <span style={{ fontWeight: "bold", color: "#38bdf8" }}>[Context Engine C2]</span>
        <input
          type="text"
          value={targetInput}
          onChange={(e) => setTargetInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !loading) launchRecon(targetInput); }}
          placeholder="Enter target domain..."
          style={{ backgroundColor: "#0f172a", border: "1px solid #475569", color: "#fff", padding: "8px 12px", borderRadius: "4px", width: "250px", fontFamily: "monospace" }}
        />
        <button
          onClick={() => launchRecon(targetInput)}
          disabled={loading}
          style={{ padding: "8px 16px", backgroundColor: "#0284c7", color: "#fff", border: "none", borderRadius: "4px", cursor: loading ? "not-allowed" : "pointer", fontWeight: "bold", opacity: loading ? 0.6 : 1 }}
        >
          {loading ? "ENGAGING..." : "ENGAGE PIPELINE"}
        </button>
        <button
          onClick={() => setShowCriticalOnly(!showCriticalOnly)}
          style={{ padding: "8px 16px", backgroundColor: showCriticalOnly ? "#dc2626" : "#475569", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer" }}
        >
          {showCriticalOnly ? "SHOW ALL ASSETS" : "FILTER CRITICAL PATHS"}
        </button>
      </div>

      <div style={{ display: "flex", flexGrow: 1, position: "relative", minHeight: "0" }}>
        <div style={{ flexGrow: 1, height: "100%" }}>
          {nodes.length === 0 && !loading ? (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "#475569", fontSize: "14px" }}>
              No graph loaded. Enter a target domain and click ENGAGE PIPELINE.
            </div>
          ) : (
            <ReactFlow nodes={displayNodes} edges={displayEdges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onNodeClick={(_, n) => setSelectedNode(n.data.fullData)} fitView colorMode="dark">
              <Background color="#334155" gap={16} />
              <Controls />
            </ReactFlow>
          )}
        </div>
        <DetailPanel nodeData={selectedNode} />
      </div>

      <div style={{ height: "150px", backgroundColor: "#020617", borderTop: "2px solid #334155", padding: "10px", overflowY: "scroll", display: "flex", flexDirection: "column", gap: "4px", fontSize: "12px", color: "#4ade80" }}>
        {logs.map((log, idx) => (
          <div key={idx}>{log}</div>
        ))}
      </div>
    </div>
  );
}

export default App;
