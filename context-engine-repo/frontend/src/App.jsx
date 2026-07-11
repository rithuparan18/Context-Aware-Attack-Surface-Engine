import { useState } from "react";
import { ReactFlow } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import DetailPanel from "./DetailPanel";
import contract from "./data/contract.json"; // (Make sure final_attack_graph.json was renamed/moved here!)

function App() {
  // State to track which node the user clicked
  const [selectedNode, setSelectedNode] = useState(null);

  // Map the JSON data to ReactFlow's format
  const nodes = contract.nodes.map((node, index) => ({
    id: node.id,
    data: { 
      label: node.label,
      fullData: node // Pass the entire node dictionary so the panel can read it
    },
    position: {
      x: index * 250, 
      y: index % 2 === 0 ? 100 : 250, // Slight stagger so they aren't in a perfect straight line
    },
  }));

  const edges = contract.edges.map((edge, index) => ({
    id: `e${index}`,
    source: edge.source,
    target: edge.target,
    animated: true, // Makes the attack paths look active
  }));

  // Handle the click event
  const handleNodeClick = (event, node) => {
    setSelectedNode(node.data.fullData);
  };

  return (
    <div style={{ display: "flex", width: "100vw", height: "100vh" }}>
      {/* Left Side: The Interactive Graph */}
      <div style={{ flexGrow: 1, height: "100%" }}>
        <ReactFlow 
          nodes={nodes} 
          edges={edges} 
          onNodeClick={handleNodeClick}
          fitView 
        />
      </div>

      {/* Right Side: The Detail Panel */}
      <DetailPanel nodeData={selectedNode} />
    </div>
  );
}

export default App;
