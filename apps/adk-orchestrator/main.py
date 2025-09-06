import os, uuid, json, logging, yaml
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, APIRouter
from pydantic import BaseModel, Field

# --- simple JSON logger ---
logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","msg":"%(message)s"}')
log = logging.getLogger("kyros")

# --- config loader ---
def load_config():
    base_path = os.path.join(os.path.dirname(__file__), "config")
    def read(name):
        p = os.path.join(base_path, name)
        return yaml.safe_load(open(p)) if os.path.exists(p) else {}
    cfg = {}
    for part in ("base.yaml","development.yaml"):
        cfg.update(read(part))
    return cfg

# --- DTOs ---
class PRRef(BaseModel):
    repo: str; pr_number: int; branch: str; head_sha: str
    html_url: Optional[str] = None

class RunRequest(BaseModel):
    pr: PRRef
    mode: str = Field(..., pattern="^(plan|implement|critic|integrate|pipeline)$")
    labels: List[str] = []
    extra: Dict[str, Any] = {}

class RunResponse(BaseModel):
    run_id: str; status: str; started_at: str; notes: Optional[str] = None

# --- very small "workflow" shim (will call engine later) ---
ROUTER_BASE = os.getenv("LLM_ROUTER_BASE", "http://localhost:4000")
MODEL_PLANNER = os.getenv("MODEL_PLANNER", "gpt-5-high")
MODEL_IMPL    = os.getenv("MODEL_IMPL", "gemini-2.5-pro")
MODEL_DEEP    = os.getenv("MODEL_DEEP", "claude-4-sonnet")
def run_with_engine(mode: str, pr: PRRef, labels: List[str], extra: Dict[str, Any]) -> str:
    needs_deep = any(l in labels for l in ["needs:deep-refactor","complex"])
    impl = MODEL_DEEP if needs_deep else MODEL_IMPL
    return f"[{mode}] {pr.repo}#{pr.pr_number} ({pr.branch}) planner={MODEL_PLANNER} impl={impl}"

# --- FastAPI setup ---
app = FastAPI(title="Kyros Orchestrator")
api = APIRouter(prefix="/v1")

@api.post("/runs/plan", response_model=RunResponse)
def runs_plan(req: RunRequest):
    run_id = str(uuid.uuid4())
    notes = run_with_engine("plan", req.pr, req.labels, req.extra)
    log.info(json.dumps({"event":"run_started","run_id":run_id,"mode":"plan"}))
    return RunResponse(run_id=run_id, status="started", started_at=datetime.utcnow().isoformat()+"Z", notes=notes)

# other run endpoints would be similar
app.include_router(api)

@app.get("/healthz")
def healthz(): return {"ok": True}

@app.get("/readyz")
def readyz(): return {"ready": True}

@app.get("/v1/config")
def cfg(): return load_config()