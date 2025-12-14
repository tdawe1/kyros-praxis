from pathlib import Path

from app.crew_runner import load_manifest, read_prompt


def test_manifest_env_substitution(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "anthropic")
    monkeypatch.setenv("MODEL_NAME", "openrouter/anthropic/claude-3.5-sonnet")

    manifests_dir = Path(__file__).resolve().parents[1] / "ai" / "crews"
    manifest = load_manifest(manifests_dir, "spec_to_tasks")

    assert manifest["model"]["provider"] == "anthropic"
    assert manifest["model"]["name"] == "openrouter/anthropic/claude-3.5-sonnet"


def test_read_prompt_accepts_prefixed_paths():
    prompts_dir = Path(__file__).resolve().parents[1] / "ai" / "prompts"
    direct = read_prompt(prompts_dir, "spec_to_tasks.md")
    prefixed = read_prompt(prompts_dir, "prompts/spec_to_tasks.md")
    assert direct == prefixed
