// Helper sub-component for clean rendering
const StatItem = ({ label, value }) => (
  <div style={{ marginBottom: "10px" }}>
    <span style={{ color: "#9ca3af", fontSize: "0.8rem" }}>{label}</span>
    <div style={{ fontSize: "1rem" }}>{value}</div>
  </div>
);

function DetailPanel({ nodeData }) {
  // Graceful empty state handling[cite: 4]
  if (!nodeData) {
    return (
      <div style={panelStyle}>
        <h2>Asset Details</h2>
        <p style={{ color: "#6b7280" }}>Select a node to inspect telemetry.</p>
      </div>
    );
  }

  const { label, roi_score, roi_breakdown, type } = nodeData;

  return (
    <div style={panelStyle}>
      <h2 style={{ color: "#60a5fa" }}>{label}</h2>
      <p>Type: {type}</p>
      
      <div style={{ padding: "15px", background: "#374151", borderRadius: "8px" }}>
        <StatItem label="Attacker ROI" value={`${roi_score}/100`} />
        
        {/* Render dynamic breakdown from backend receipt */}
        {roi_breakdown && Object.entries(roi_breakdown).map(([k, v]) => (
          <StatItem key={k} label={k.replace("_", " ")} value={v} />
        ))}
      </div>
    </div>
  );
}

// Optimized static styles
const panelStyle = {
  width: "350px",
  height: "100vh",
  backgroundColor: "#1f2937",
  color: "white",
  padding: "20px",
  borderLeft: "2px solid #4b5563",
  overflowY: "auto"
};

export default DetailPanel;
