import React, { useState, useEffect, useCallback, useMemo } from "react";
import { ReactFlow, Controls, Background, applyNodeChanges, applyEdgeChanges } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import dagre from "dagre";

import DetailPanel from "./components/DetailPanel";

// SREENIVAS & ABINAYA: Task 2 (Dagre Auto-Layout Engine)
const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const getLayoutedElements = (nodes, edges, direction = 'LR') => {
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 180, height: 70 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - 180 / 2,
        y: nodeWithPosition.y - 70 / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};

function App() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // VANITHA: Task 2 (Risk-filtering toggle)
  const [showCriticalOnly, setShowCriticalOnly] = useState(false);

  // ABINAYA: Task 1 (Live API Fetching)
  const fetchGraphData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch("http://127.0.0.1:8000/api/graph");
      if (!response.ok) throw new Error("Backend API unreachable");
      const data = await response.json();

      const initialNodes = data.nodes.map((node) => ({
        id: String(node.id),
        data: { label: node.label || "Unknown Node", fullData: node },
        position: { x: 0, y: 0 }, // Dagre handles actual placement
        style: { 
          background: (node.roi_score || 0) > 60 ? "#ef4444" : "#10b981", 
          color: "#fff",
          borderRadius: "8px",
          padding: "10px",
          width: 170,
          textAlign: "center",
          // Highlight the chokepoints visually
          border: node.is_chokepoint ? "3px solid #fbbf24" : "1px solid #374151",
          boxShadow: node.is_chokepoint ? "0 0 15px rgba(251, 191, 36, 0.5)" : "none"
        },
      }));

      const initialEdges = (data.links || []).map((link, index) => ({
        id: `e${index}-${link.source}-${link.target}`,
        source: String(link.source),
        target: String(link.target),
        animated: true,
        label: link.relationship,
        style: { stroke: "#9ca3af", strokeWidth: 2 },
        labelStyle: { fill: "#d1d5db", fontWeight: "bold" },
      }));

      // Apply the Dagre math before setting state
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(initialNodes, initialEdges);
      
      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
    } catch (error) {
      console.error("Failed to fetch graph:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Ignite pipeline on initial load
  useEffect(() => {
    fetchGraphData();
  }, [fetchGraphData]);

  const onNodesChange = useCallback((changes) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
  const onEdgesChange = useCallback((changes) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);

  // Filter logic for the UI toggle
  const displayNodes = useMemo(() => {
    if (!showCriticalOnly) return nodes;
    return nodes.filter(n => n.data.fullData.roi_score > 60 || n.data.fullData.is_chokepoint);
  }, [nodes, showCriticalOnly]);

  const displayEdges = useMemo(() => {
    if (!showCriticalOnly) return edges;
    const visibleNodeIds = new Set(displayNodes.map(n => n.id));
    return edges.filter(e => visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target));
  }, [edges, displayNodes]);

  return (
    <div style={{ display: "flex", width: "100vw", height: "100vh", backgroundColor: "#111827" }}>
      <div style={{ flexGrow: 1, height: "100%", position: "relative" }}>
        
        {/* VANITHA: Task 1 & 2 (Top Control Bar) */}
        <div style={{ position: "absolute", top: 20, left: 20, zIndex: 10, display: "flex", gap: "10px" }}>
          <button 
            onClick={fetchGraphData}
            style={{ padding: "8px 16px", backgroundColor: "#3b82f6", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "bold" }}
          >
            {loading ? "Refreshing Engine..." : "Refresh Pipeline"}
          </button>
          <button 
            onClick={() => setShowCriticalOnly(!showCriticalOnly)}
            style={{ padding: "8px 16px", backgroundColor: showCriticalOnly ? "#ef4444" : "#374151", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", transition: "0.2s" }}
          >
            {showCriticalOnly ? "Show All Assets" : "Show Critical Paths Only"}
          </button>
        </div>

        <ReactFlow 
          nodes={displayNodes} 
          edges={displayEdges} 
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={(_, node) => setSelectedNode(node.data.fullData)}
          fitView
          colorMode="dark"
        >
          <Background color="#4b5563" />
          <Controls />
        </ReactFlow>
      </div>
      <DetailPanel nodeData={selectedNode} />
    </div>
  );
}

export default App;