import json
import logging
import os

# Import Agent SDK components
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml
from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "packages"))

from agent_sdk.capabilities.negotiator import CapabilityNegotiator
from agent_sdk.contracts import AgentBase, AgentContext
from agent_sdk.memory.sqlite_store import SQLiteMemoryStore
from agent_sdk.sandbox.subprocess_executor import SubprocessSandbox
from agent_sdk.tools.protocol import ToolRegistry

# --- simple JSON logger ---
logging.basicConfig(
    level=logging.INFO, format='{"level":"%(levelname)s","msg":"%(message)s"}'
)
log = logging.getLogger("kyros")


# --- Pydantic Settings Configuration ---
class OrchestratorConfig(BaseModel):
    workers: int = 4
    timeout_seconds: int = 300


class SandboxConfig(BaseModel):
    enabled: bool = True
    timeout_seconds: int = 30
    memory_limit_mb: int = 512


class MemoryConfig(BaseModel):
    vector_store: bool = False
    history_limit: int = 100


class ToolsConfig(BaseModel):
    auto_discover: bool = True
    validation: str = "strict"


class AgentsConfig(BaseModel):
    sandbox: SandboxConfig = SandboxConfig()
    memory: MemoryConfig = MemoryConfig()
    tools: ToolsConfig = ToolsConfig()


class LogConfig(BaseModel):
    json_format: bool = True


class ServicesConfig(BaseModel):
    orchestrator: OrchestratorConfig = OrchestratorConfig()


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    services: ServicesConfig = ServicesConfig()
    agents: AgentsConfig = AgentsConfig()
    log: LogConfig = LogConfig()

    # Environment variables for model configuration
    llm_router_base: str = "http://localhost:4000"
    model_planner: str = "gpt-5-high"
    model_impl: str = "gemini-2.5-pro"
    model_deep: str = "claude-4-sonnet"


# --- config loader ---
def load_config():
    """Load configuration from YAML files and environment variables"""
    base_path = os.path.join(os.path.dirname(__file__), "config")

    def read_yaml(name):
        p = os.path.join(base_path, name)
        return yaml.safe_load(open(p)) if os.path.exists(p) else {}

    # Load YAML configs
    yaml_config = {}
    for part in ("base.yaml", "development.yaml"):
        yaml_config.update(read_yaml(part))

    # Create settings instance
    settings = AppConfig()

    # Merge YAML config with settings
    config_dict = settings.model_dump()

    # Override with YAML values if they exist
    if "services" in yaml_config:
        config_dict["services"].update(yaml_config["services"])
    if "agents" in yaml_config:
        config_dict["agents"].update(yaml_config["agents"])
    if "log" in yaml_config:
        config_dict["log"].update(yaml_config["log"])

    return config_dict


# --- DTOs ---
class PRRef(BaseModel):
    repo: str
    pr_number: int
    branch: str
    head_sha: str
    html_url: Optional[str] = None


class RunRequest(BaseModel):
    pr: PRRef
    mode: str = Field(..., pattern="^(plan|implement|critic|integrate|pipeline)$")
    labels: List[str] = []
    extra: Dict[str, Any] = {}


class RunResponse(BaseModel):
    run_id: str
    status: str
    started_at: str
    notes: Optional[str] = None


# --- Global configuration instance ---
config = load_config()


# --- Agent SDK Integration ---
class AgentOrchestrator:
    """Orchestrator for managing agents and their interactions."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.memory_store = SQLiteMemoryStore(
            db_path=config.get("agents", {})
            .get("memory", {})
            .get("db_path", "data/kyros.db")
        )
        self.tool_registry = ToolRegistry()
        self.sandbox = SubprocessSandbox()
        self.negotiator = CapabilityNegotiator()
        self.agents: Dict[str, AgentBase] = {}

        # Initialize with example agent if available
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize available agents."""
        try:
            from agent_sdk.runners.example_agent import ExampleAgent

            example_agent = ExampleAgent(self.memory_store, self.sandbox)
            self.register_agent(example_agent)
        except ImportError:
            log.warning("Example agent not available")

    def register_agent(self, agent: AgentBase):
        """Register an agent with the orchestrator."""
        agent_id = agent.get_name()
        self.agents[agent_id] = agent

        # Register with capability negotiator
        capabilities = agent.capabilities()
        self.negotiator.register_agent(agent, capabilities)

        log.info(
            json.dumps(
                {
                    "event": "agent_registered",
                    "agent_id": agent_id,
                    "capabilities": capabilities,
                }
            )
        )

    async def execute_task(self, task: Dict[str, Any], mode: str) -> Dict[str, Any]:
        """Execute a task using the best available agent."""
        # Find best agent for the task
        best_agent, missing_caps = self.negotiator.match(task)

        if not best_agent:
            return {
                "status": "error",
                "error": "No suitable agent found",
                "missing_capabilities": missing_caps,
            }

        # Create agent context
        tools_as_dicts = [tool.model_dump() for tool in self.tool_registry.list_all()]
        context = AgentContext(
            task=task,
            tools=tools_as_dicts,
            memory={},
            telemetry={"mode": mode, "timestamp": datetime.utcnow().isoformat()},
            tenant_id=task.get("tenant_id"),
        )

        # Execute with the selected agent
        try:
            result: Dict[str, Any] = await best_agent.execute(context)

            # Log the interaction
            log.info(
                json.dumps(
                    {
                        "event": "task_executed",
                        "agent_id": best_agent.get_name(),
                        "mode": mode,
                        "task_id": task.get("id", "unknown"),
                        "status": result.get("status", "unknown"),
                        "rationale_summary": result.get("message", {}).get(
                            "rationale_summary", ""
                        ),
                    }
                )
            )

            return result

        except Exception as e:
            log.error(
                json.dumps(
                    {
                        "event": "task_execution_error",
                        "agent_id": best_agent.get_name(),
                        "error": str(e),
                        "task_id": task.get("id", "unknown"),
                    }
                )
            )
            return {
                "status": "error",
                "error": str(e),
                "agent_id": best_agent.get_name(),
            }

    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all registered agents."""
        status: Dict[str, Any] = self.negotiator.get_agent_status()
        return status

    async def cleanup(self):
        """Clean up resources."""
        await self.sandbox.cleanup()


# --- Global orchestrator instance ---
orchestrator = AgentOrchestrator(config)


# --- very small "workflow" shim (will call engine later) ---
def run_with_engine(
    mode: str, pr: PRRef, labels: List[str], extra: Dict[str, Any]
) -> str:
    """Simulate running a workflow with the engine"""
    needs_deep = any(label in labels for label in ["needs:deep-refactor", "complex"])
    impl = (
        config.get("model_deep", "claude-4-sonnet")
        if needs_deep
        else config.get("model_impl", "gemini-2.5-pro")
    )
    planner = config.get("model_planner", "gpt-5-high")
    return (
        f"[{mode}] {pr.repo}#{pr.pr_number} ({pr.branch}) planner={planner} impl={impl}"
    )


# --- FastAPI setup ---
app = FastAPI(
    title="Kyros Orchestrator API",
    version="1.0.0",
    description="API for managing agent runs and system configuration",
)
api = APIRouter(prefix="/v1")


@api.post("/runs/plan", response_model=RunResponse)
async def runs_plan(req: RunRequest):
    """Start a plan run for a pull request"""
    try:
        run_id = str(uuid.uuid4())

        # Create task for agent execution
        task = {
            "id": run_id,
            "type": "plan",
            "description": f"Plan implementation for {req.pr.repo}#{req.pr.pr_number}",
            "pr": req.pr.dict(),
            "labels": req.labels,
            "extra": req.extra,
            "capabilities": ["planning", "analysis"],
            "priority": 1,
        }

        # Execute task using orchestrator
        result = await orchestrator.execute_task(task, "plan")

        # Extract rationale summary for logging
        rationale_summary = ""
        if "message" in result and isinstance(result["message"], dict):
            rationale_summary = result["message"].get("rationale_summary", "")
        elif "rationale_summary" in result:
            rationale_summary = result["rationale_summary"]

        log.info(
            json.dumps(
                {
                    "event": "run_started",
                    "run_id": run_id,
                    "mode": "plan",
                    "repo": req.pr.repo,
                    "pr_number": req.pr.pr_number,
                    "status": result.get("status", "unknown"),
                    "rationale_summary": rationale_summary,
                }
            )
        )

        return RunResponse(
            run_id=run_id,
            status=result.get("status", "started"),
            started_at=datetime.utcnow().isoformat() + "Z",
            notes=f"Agent execution: {result.get('status', 'unknown')}",
        )
    except Exception as e:
        log.error(json.dumps({"event": "run_error", "error": str(e)}))
        raise HTTPException(status_code=500, detail="Internal server error")


@api.post("/runs/implement", response_model=RunResponse)
async def runs_implement(req: RunRequest):
    """Start an implement run for a pull request"""
    try:
        run_id = str(uuid.uuid4())

        # Create task for agent execution
        task = {
            "id": run_id,
            "type": "implement",
            "description": f"Implement changes for {req.pr.repo}#{req.pr.pr_number}",
            "pr": req.pr.dict(),
            "labels": req.labels,
            "extra": req.extra,
            "capabilities": ["implementation", "coding"],
            "priority": 2,
        }

        # Execute task using orchestrator
        result = await orchestrator.execute_task(task, "implement")

        log.info(
            json.dumps(
                {
                    "event": "run_started",
                    "run_id": run_id,
                    "mode": "implement",
                    "repo": req.pr.repo,
                    "pr_number": req.pr.pr_number,
                    "status": result.get("status", "unknown"),
                }
            )
        )

        return RunResponse(
            run_id=run_id,
            status=result.get("status", "started"),
            started_at=datetime.utcnow().isoformat() + "Z",
            notes=f"Agent execution: {result.get('status', 'unknown')}",
        )
    except Exception as e:
        log.error(json.dumps({"event": "run_error", "error": str(e)}))
        raise HTTPException(status_code=500, detail="Internal server error")


@api.post("/runs/critic", response_model=RunResponse)
async def runs_critic(req: RunRequest):
    """Start a critic run for a pull request"""
    try:
        run_id = str(uuid.uuid4())

        # Create task for agent execution
        task = {
            "id": run_id,
            "type": "critic",
            "description": f"Review and critique {req.pr.repo}#{req.pr.pr_number}",
            "pr": req.pr.dict(),
            "labels": req.labels,
            "extra": req.extra,
            "capabilities": ["review", "critique", "analysis"],
            "priority": 1,
        }

        # Execute task using orchestrator
        result = await orchestrator.execute_task(task, "critic")

        log.info(
            json.dumps(
                {
                    "event": "run_started",
                    "run_id": run_id,
                    "mode": "critic",
                    "repo": req.pr.repo,
                    "pr_number": req.pr.pr_number,
                    "status": result.get("status", "unknown"),
                }
            )
        )

        return RunResponse(
            run_id=run_id,
            status=result.get("status", "started"),
            started_at=datetime.utcnow().isoformat() + "Z",
            notes=f"Agent execution: {result.get('status', 'unknown')}",
        )
    except Exception as e:
        log.error(json.dumps({"event": "run_error", "error": str(e)}))
        raise HTTPException(status_code=500, detail="Internal server error")


@api.get("/agents/status")
async def get_agents_status():
    """Get status of all registered agents"""
    try:
        status = await orchestrator.get_agent_status()
        return {"agents": status}
    except Exception as e:
        log.error(json.dumps({"event": "agent_status_error", "error": str(e)}))
        raise HTTPException(status_code=500, detail="Internal server error")


# Include the v1 API router
app.include_router(api)

# Response models for basic endpoints
class HealthResponse(BaseModel):
    ok: bool = True

class ReadyResponse(BaseModel):
    ready: bool = True

@app.get("/healthz", response_model=HealthResponse)
def healthz():
    """Health check endpoint"""
    return {"ok": True}

@app.get("/readyz", response_model=ReadyResponse)
def readyz():
    """Readiness check endpoint"""
    return {"ready": True}


@app.get("/v1/config")
def get_config():
    """Get orchestrator configuration"""
    return config


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    await orchestrator.cleanup()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
