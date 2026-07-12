"""
Single Layer 4 service.
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from typing import Any, Dict, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from engine.graph_engine import GraphEngine
from ingestion.ingestion import IngestionPipeline, validate_target

app = FastAPI(title="Context-Aware Attack Surface Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_pipeline = IngestionPipeline()

# BUGFIX: the frontend sends ?target=<domain>, but this endpoint used to
# ignore it completely and always run against a hardcoded "bank.local" —
# typing a different target in the UI silently did nothing. The cache is
# now keyed BY target too: previously a single shared cache entry meant
# fetching two different targets within the 5s TTL window would return
# one target's data for the other.
_CACHE_TTL_SEC = 5
_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}  # target -> (timestamp, payload)


async def get_payload(target: str) -> Dict[str, Any]:
    now = time.time()
    cached = _cache.get(target)
    if cached and (now - cached[0]) < _CACHE_TTL_SEC:
        return cached[1]

    raw_nodes = await _pipeline.execute(target, "./context-engine-repo")
    engine = GraphEngine()
    engine.ingest_nodes(raw_nodes)
    payload = engine.export()

    _cache[target] = (now, payload)
    return payload


@app.get("/api/graph")
async def get_graph(target: str = "bank.local"):
    try:
        target = validate_target(target)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return await get_payload(target)


@app.get("/api/graph/node/{node_id}")
async def get_node(node_id: str, target: str = "bank.local"):
    try:
        target = validate_target(target)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    payload = await get_payload(target)
    for node in payload["nodes"]:
        if node["id"] == node_id:
            return node
    raise HTTPException(status_code=404, detail=f"Node {node_id} not found")


@app.get("/api/graph/chokepoints")
async def get_chokepoints(target: str = "bank.local"):
    try:
        target = validate_target(target)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    payload = await get_payload(target)
    return {
        "summary": payload["chokepoint_summary"],
        "nodes": [n for n in payload["nodes"] if n.get("is_chokepoint")],
    }


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "layer": 4}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
