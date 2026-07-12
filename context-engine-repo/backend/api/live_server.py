from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Ensure Python can find the engine folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.correlation_live import CorrelationEngine, Node
from engine.risk_engine_live import RiskEngineLive

app = FastAPI(title="Context Engine - Live")

# CORS config to allow the local Vite server (localhost:5173) to fetch data
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/graph")
async def get_live_graph():
    """Ignites the pipeline and returns the fully mapped frontend schema."""
    
    # 1. Initialize the live correlation engine
    corr_engine = CorrelationEngine()
    
    # 2. Inject simulated live queue data (Handoff from Pod 1)
    mock_nodes = [
        Node("n1", "ip", "192.168.1.100", "nmap", {"ports": [80, 443]}),
        Node("n2", "vulnerability", "CVE-2024-Unauth-RCE", "nuclei", {"cvss": 9.8}),
        Node("n3", "database", "Prod-Customer-DB", "nmap", {"ports": [5432]})
    ]
    
    for n in mock_nodes:
        corr_engine.ingest_node(n)
        
    # Triggering deterministic relationships 
    corr_engine.graph.add_edge("n1", "n2", relationship="has_vulnerability", confidence=1.0)
    corr_engine.graph.add_edge("n2", "n3", relationship="compromises", confidence=0.95)

    # 3. Apply the live Risk Engine math
    risk_engine = RiskEngineLive(corr_engine.graph)
    annotated_graph = risk_engine.execute()

    # 4. Export the clean JSON payload back through Sreenivas's exporter
    corr_engine.graph = annotated_graph 
    return corr_engine.export_to_frontend_schema()

if __name__ == "__main__":
    import uvicorn
    # Launch the API from this file
    uvicorn.run("live_server:app", host="127.0.0.1", port=8000, reload=True)