from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Literal

class Edge(BaseModel):
    id: str
    source: str
    target: str
    relationship: Literal["belongs_to", "owned_by", "grants_access_to", "resolves_to", "shares_infra"]
    confidence: float = Field(ge=0.0, le=1.0)

class Node(BaseModel):
    id: str
    type: Literal["domain", "subdomain", "ip", "port", "credential", "s3_bucket", "service", "employee", "cve"]
    label: str
    source_tool: str
    attributes: Dict[str, Any]
    roi_score: float = Field(default=0.0, ge=0.0, le=100.0)
    roi_breakdown: Dict[str, float] = {}
    is_chokepoint: bool = False
    chokepoint_rank: Optional[int] = None

class GraphMeta(BaseModel):
    target: str
    generated_at: str
    scan_id: str

class GraphContract(BaseModel):
    meta: GraphMeta
    nodes: List[Node]
    edges: List[Edge]
    chokepoint_summary: Dict[str, Any] = {}