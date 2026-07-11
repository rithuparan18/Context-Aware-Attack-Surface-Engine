function DetailPanel({ nodeData }) {
  return (
    <div
      style={{
        width: "350px",
        height: "100vh",
        backgroundColor: "#1f2937",
        color: "white",
        padding: "20px",
        position: "relative",
        borderLeft: "2px solid gray",
        overflowY: "auto"
      }}
    >
      <h2>Asset Details</h2>
      <hr />
      
      {/* If no node is clicked, show the prompt */}
      {!nodeData ? (
        <p style={{ color: "#9ca3af" }}>Select a node on the canvas to view telemetry.</p>
      ) : (
        /* If a node is clicked, render its backend data */
        <div>
          <h3 style={{ color: "#60a5fa" }}>{nodeData.label}</h3>
          <p><strong>Type:</strong> <span style={{ textTransform: "capitalize" }}>{nodeData.type}</span></p>
          <p><strong>Source:</strong> {nodeData.source_tool}</p>
          
          <div style={{ marginTop: "20px", padding: "10px", backgroundColor: "#374151", borderRadius: "5px" }}>
            <h4 style={{ margin: "0 0 10px 0" }}>Attacker ROI Score</h4>
            <div style={{ fontSize: "2rem", color: nodeData.roi_score > 60 ? "#ef4444" : "#10b981" }}>
              {nodeData.roi_score}/100
            </div>
            
            {/* Render the math breakdown if it exists */}
            {nodeData.roi_breakdown && (
              <ul style={{ fontSize: "0.85rem", color: "#d1d5db", paddingLeft: "20px" }}>
                <li>Base: {nodeData.roi_breakdown.base_score}</li>
                <li>Internet Bonus: +{nodeData.roi_breakdown.internet_facing_bonus}</li>
                <li>Criticality Bonus: +{nodeData.roi_breakdown.criticality_bonus}</li>
                <li>WAF Penalty: {nodeData.roi_breakdown.waf_penalty}</li>
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default DetailPanel;
