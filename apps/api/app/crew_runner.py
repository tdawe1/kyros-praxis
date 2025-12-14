import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any, Dict

import yaml

from .models import RunStatus
from .storage import store
from .core.config import settings


class ManifestError(Exception):
    pass


_ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)(:-([^}]*))?\}")


def _substitute_env(value: str) -> str:
    def repl(match: re.Match[str]) -> str:
        var = match.group(1)
        default = match.group(3) or ""
        return os.getenv(var, default)

    return _ENV_PATTERN.sub(repl, value)


def _resolve_env(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _resolve_env(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_env(v) for v in obj]
    if isinstance(obj, str):
        return _substitute_env(obj)
    return obj


def load_manifest(manifests_dir: Path, crew_id: str) -> Dict[str, Any]:
    path = manifests_dir / f"{crew_id}.yaml"
    if not path.exists():
        raise ManifestError(f"Crew manifest not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return _resolve_env(data)


def read_prompt(prompts_dir: Path, rel_path: str) -> str:
    # Normalize relative path; allow manifests to specify 'spec.md' or 'prompts/spec.md'
    p = Path(rel_path)
    if p.is_absolute():
        path = p
    else:
        rel = str(p)
        if rel.startswith("prompts/"):
            rel = rel.split("/", 1)[1]
        path = prompts_dir / rel
    if not path.exists():
        raise ManifestError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")


async def simulate_run(run_id: str, manifest: Dict[str, Any], payload: Dict[str, Any]) -> None:
    await store.update_status(run_id, RunStatus.running)
    await store.add_event(run_id, {"type": "log", "message": f"Loaded crew: {manifest.get('name', 'unknown')}"})
    await asyncio.sleep(0.5)
    await store.add_event(run_id, {"type": "log", "message": f"Input received: {payload}"})
    await asyncio.sleep(0.5)
    # Placeholder result
    result = {"artifacts": [{"path": "generated/tasks.json", "count": 3}]}
    await store.update_status(run_id, RunStatus.succeeded, result=result)


def _configure_provider_env(manifest: Dict[str, Any]) -> tuple[str | None, str | None]:
    """
    Configure environment variables for the LLM provider specified in the manifest.
    
    Supports: openrouter, openai, vertex, bedrock, azure
    """
    from .llm_providers import get_provider_config, configure_environment
    
    model_cfg = manifest.get("model", {}) or {}
    provider = str(model_cfg.get("provider", settings.MODEL_PROVIDER or "openrouter")).lower()
    model_name = str(model_cfg.get("name", settings.MODEL_NAME or "gpt-4o-mini"))
    
    # Use provider-specific model if specified in manifest
    provider_model_key = f"{provider}_model"
    if provider_model_key in model_cfg:
        model_name = model_cfg[provider_model_key]
    
    # Get and apply provider configuration
    config = get_provider_config(provider, model_name)
    configure_environment(config)
    
    return provider, config.model_name


async def run_with_crewai(run_id: str, manifest: Dict[str, Any], payload: Dict[str, Any]) -> bool:
    # Configure provider env before imports/initialization
    provider, model_name = _configure_provider_env(manifest)
    key_present = bool(os.getenv("OPENAI_API_KEY"))
    await store.add_event(run_id, {"type": "log", "message": f"Provider: {provider}, model: {model_name}, key_present={key_present}"})

    try:
        from crewai import Agent, Task, Crew, Process  # type: ignore
    except Exception as e:  # crewai not installed
        await store.add_event(run_id, {"type": "log", "message": f"CrewAI unavailable: {e}"})
        return False

    await store.update_status(run_id, RunStatus.running)
    await store.add_event(run_id, {"type": "log", "message": "Starting CrewAI run"})

    prompts_dir = Path(__file__).resolve().parent.parent / "ai" / "prompts"

    # Minimal: take the first role and a single task
    roles = manifest.get("roles", [])
    if not roles:
        await store.add_event(run_id, {"type": "error", "message": "Manifest has no roles"})
        await store.update_status(run_id, RunStatus.failed)
        return True

    role = roles[0]
    role_name = role.get("name", "planner")
    goal = role.get("goal", "Plan tasks from spec")
    prompt_path = role.get("prompt")
    if not prompt_path:
        await store.add_event(run_id, {"type": "error", "message": "Role missing prompt path"})
        await store.update_status(run_id, RunStatus.failed)
        return True

    base_prompt = read_prompt(prompts_dir, prompt_path)
    user_prompt = payload.get("prompt") or ""
    final_prompt = f"{base_prompt}\n\nUser input:\n{user_prompt}".strip()

    # Define agent and task
    agent = Agent(role=role_name, goal=goal, backstory="Kyros Praxis planning agent", verbose=True, allow_delegation=False)
    task = Task(description=final_prompt, agent=agent, expected_output="Return JSON with key 'tasks' as specified.")

    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential)

    loop = asyncio.get_running_loop()
    try:
        # kickoff may perform blocking calls; run in executor
        # Include model hint in inputs for any tasks that consult it
        inputs = {**payload, "model": model_name}
        result_text = await loop.run_in_executor(None, lambda: crew.kickoff(inputs=inputs))
        parsed: Dict[str, Any] | None = None
        try:
            if isinstance(result_text, str):
                parsed = json.loads(result_text)
            elif hasattr(result_text, "raw") and isinstance(result_text.raw, str):
                parsed = json.loads(result_text.raw)
        except Exception:
            parsed = None

        if parsed is None:
            await store.add_event(run_id, {"type": "log", "message": "Non-JSON result; storing raw output"})
            parsed = {"raw": str(result_text)}

        await store.update_status(run_id, RunStatus.succeeded, result=parsed)
        return True
    except Exception as e:
        await store.add_event(run_id, {"type": "error", "message": f"CrewAI run failed: {e}"})
        await store.update_status(run_id, RunStatus.failed)
        return True


async def run_crew(run_id: str, crew_id: str, payload: Dict[str, Any]) -> None:
    rec = await store.get_run(run_id)
    if not rec:
        return
    manifests_dir = Path(__file__).resolve().parent.parent / "ai" / "crews"
    try:
        manifest = load_manifest(manifests_dir, crew_id)
    except ManifestError as e:
        await store.add_event(run_id, {"type": "error", "message": str(e)})
        await store.update_status(run_id, RunStatus.failed)
        return

    # Prefer real CrewAI if available; otherwise simulate
    used_crewai = await run_with_crewai(run_id, manifest, payload)
    if not used_crewai:
        await simulate_run(run_id, manifest, payload)

