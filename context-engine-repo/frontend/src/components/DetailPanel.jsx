import React from "react";

function DetailPanel({ nodeData }) {
  if (!nodeData) {
    return (
      <div style={{ width: "350px", backgroundColor: "#1e293b", borderLeft: "2px solid #334155", padding: "20px", color: "#94a3b8", display: "flex", flexDirection: "column" }}>
        <h2 style={{ color: "#f8fafc", margin: "0 0 10px 0" }}>Threat Telemetry</h2>
        <p>Awaiting asset selection...</p>
      </div>
    );
  }

  const { type, label, source_tool, roi_score, roi_breakdown, attributes, is_chokepoint } = nodeData;

  return (
    <div style={{ width: "350px", backgroundColor: "#1e293b", borderLeft: "2px solid #334155", padding: "20px", color: "#e2e8f0", display: "flex", flexDirection: "column", overflowY: "auto" }}>
      <h2 style={{ color: "#38bdf8", margin: "0 0 5px 0", wordBreak: "break-all" }}>{label}</h2>
      
      <div style={{ display: "flex", gap: "10px", marginBottom: "20px" }}>
        <span style={{ padding: "4px 8px", backgroundColor: "#334155", borderRadius: "4px", fontSize: "12px", fontWeight: "bold", textTransform: "uppercase" }}>{type}</span>
        <span style={{ padding: "4px 8px", backgroundColor: "#0f172a", borderRadius: "4px", fontSize: "12px", color: "#94a3b8" }}>Source: {source_tool}</span>
      </div>

      {is_chokepoint && (
        <div style={{ backgroundColor: "rgba(251, 191, 36, 0.1)", border: "1px solid #fbbf24", color: "#fbbf24", padding: "10px", borderRadius: "6px", marginBottom: "20px", fontWeight: "bold", fontSize: "14px" }}>
          ⚠️ CRITICAL CHOKEPOINT IDENTIFIED
          <div style={{ fontSize: "12px", fontWeight: "normal", marginTop: "4px", color: "#d97706" }}>Severing this node breaks the maximum number of attack paths.</div>
        </div>
      )}

      <div style={{ backgroundColor: "#0f172a", padding: "15px", borderRadius: "6px", marginBottom: "20px" }}>
        <h3 style={{ margin: "0 0 10px 0", fontSize: "14px", color: "#94a3b8", borderBottom: "1px solid #334155", paddingBottom: "5px" }}>Attacker ROI Score</h3>
        <div style={{ fontSize: "36px", fontWeight: "bold", color: roi_score > 60 ? "#ef4444" : "#10b981", marginBottom: "10px" }}>
          {roi_score || 0}<span style={{ fontSize: "18px", color: "#64748b" }}> /100</span>
        </div>
        
        {roi_breakdown && (
          <div style={{ fontSize: "13px", display: "flex", flexDirection: "column", gap: "6px" }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}><span>Base Score:</span> <span>+{roi_breakdown.base_score}</span></div>
            <div style={{ display: "flex", justifyContent: "space-between" }}><span>Criticality Bonus:</span> <span>+{roi_breakdown.criticality_bonus}</span></div>
            <div style={{ display: "flex", justifyContent: "space-between" }}><span>WAF Penalty:</span> <span style={{ color: "#ef4444" }}>{roi_breakdown.waf_penalty}</span></div>
            {roi_breakdown.chokepoint_bonus > 0 && (
              <div style={{ display: "flex", justifyContent: "space-between", color: "#fbbf24" }}><span>Chokepoint Multiplier:</span> <span>+{roi_breakdown.chokepoint_bonus}</span></div>
            )}
            {roi_breakdown.cascade_bonus > 0 && (
              <div style={{ display: "flex", justifyContent: "space-between", color: "#f87171" }}><span>Risk Cascade (Inherited):</span> <span>+{roi_breakdown.cascade_bonus}</span></div>
            )}
          </div>
        )}
      </div>

      {attributes && Object.keys(attributes).length > 0 && (
        <div>
          <h3 style={{ margin: "0 0 10px 0", fontSize: "14px", color: "#94a3b8", borderBottom: "1px solid #334155", paddingBottom: "5px" }}>Raw Attributes</h3>
          <pre style={{ backgroundColor: "#020617", padding: "10px", borderRadius: "6px", fontSize: "12px", overflowX: "auto", color: "#a7f3d0", margin: "0" }}>
            {JSON.stringify(attributes, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

export default DetailPanel;