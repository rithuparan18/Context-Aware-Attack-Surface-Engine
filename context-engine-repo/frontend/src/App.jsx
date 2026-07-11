import { useState, useMemo } from "react";
import { ReactFlow, Controls, Background } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import DetailPanel from "./DetailPanel";
// Ensure this path matches where you saved the backend output
import graphData from "./data/final_attack_graph.json";

function App() {
  const [selectedNode, setSelectedNode] = useState(null);

  // Memoize graph structure to prevent unnecessary re-renders[cite: 6]
  const { nodes, edges } = useMemo(() => {
    const n = graphData.nodes.map((node, index) => ({
      id: node.id,
      position: { x: index * 250, y: 150 },
      data: { label: node.label, fullData: node },
      // Dynamic risk styling: High risk (ROI > 60) turns red
      style: { 
        background: node.roi_score > 60 ? "#ef4444" : "#10b981", 
        color: "#fff",
        borderRadius: "8px",
        padding: "10px",
        width: 150
      },
    }));

    const e = graphData.links.map((link, index) => ({
      id: `e${index}`,
      source: link.source,
      target: link.target,
      animated: true,
      style: { stroke: "#9ca3af", strokeWidth: 2 },
    }));

    return { nodes: n, edges: e };
  }, []);

  return (
    <div style={{ display: "flex", width: "100vw", height: "100vh" }}>
      <div style={{ flexGrow: 1 }}>
        <ReactFlow 
          nodes={nodes} 
          edges={edges} 
          onNodeClick={(_, node) => setSelectedNode(node.data.fullData)}
          fitView
        >
          <Background />
          <Controls />
        </ReactFlow>
      </div>
      <DetailPanel nodeData={selectedNode} />
    </div>
  );
}

export default App;
