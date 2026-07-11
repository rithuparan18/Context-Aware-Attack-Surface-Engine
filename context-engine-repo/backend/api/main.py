import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Context-Aware Attack Surface Engine API",
    description="Layer 3 Presentation API providing graph analysis telemetry.",
    version="1.0.0"
)

# Enable CORS so Pod 4's local React instance can call our endpoints smoothly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Relative pathway lookup to find the root contract file
CONTRACT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../contract.json"))

@app.get("/api/graph")
async def get_graph():
    """
    Day 1 Baseline Endpoint: Serves the canonical contract.json structure 
    directly from disk to unblock frontend visualization development.
    """
    if not os.path.exists(CONTRACT_PATH):
        raise HTTPException(
            status_code=404, 
            detail=f"API Contract file missing at structural path: {CONTRACT_PATH}. Ensure contract.json exists in root."
        )
        
    try:
        with open(CONTRACT_PATH, "r") as file:
            contract_data = json.load(file)
        return contract_data
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500, 
            detail="Root contract.json file corrupted or violates valid JSON formatting rules."
        )

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "layer": 3, "pod": "Risk Engine"}
