import json
from typing import Dict, List

import yaml
from jsonschema import validate


def load_handoff_schema() -> Dict:
    """
    Load the handoff schema from YAML.
    """
    with open("docs/schemas/handoff-card.yaml", "r") as f:
        schema_text = f.read()
    return yaml.safe_load(schema_text)


def generate_handoff(
    mode: str,
    message: str,
    context: str,
    scope: str,
    completion_signal: str,
    parent_context: str,
    dependencies: List[str],
    superseding_statement: str,
) -> Dict:
    """
    Generate a handoff card dict from parameters, based on the schema.
    """
    handoff = {
        "mode": mode,
        "message": message,
        "context": context,
        "scope": scope,
        "completion_signal": completion_signal,
        "parent_context": parent_context,
        "dependencies": dependencies,
        "superseding_statement": superseding_statement,
    }
    schema = load_handoff_schema()
    validate(instance=handoff, schema=schema)
    return handoff


def format_for_new_task(handoff: Dict) -> str:
    """
    Format the handoff as XML for the new_task tool.
    """
    return f"""<new_task>
<mode>{handoff["mode"]}</mode>
<message>{handoff["message"]}</message>
</new_task>"""


def emit_delegation_event(handoff: Dict) -> Dict:
    """
    Format event for delegation (to be emitted via docs-emit-event.py).
    """
    return {
        "ts": "now",  # Replace with actual timestamp
        "event": "handoff_delegated",
        "actor": "orchestrator",
        "target": handoff["mode"],
        "details": handoff,
    }


if __name__ == "__main__":
    # Sample handoff from orchestrator to code mode using backend-current-plan.md snippet
    snippet = (
        "Models: `Task {{id, title, description, version, created_at}}` "
        "(SQLAlchemy sync, SQLite default). Endpoints: `GET /healthz`: DB ping "
        'returns `{{status:"ok"}}`. `POST /collab/tasks`: create; returns '
        "body `{{id,title,description,version}}` and header `ETag` (SHA‑256 "
        "of canonical JSON). `GET /collab/state/tasks`: list items; returns "
        "header `ETag` for the full payload."
    )
    handoff = generate_handoff(
        mode="code",
        message="Implement the handoff schema based on this handoff.",
        context=f"Snippet from backend-current-plan.md: {snippet}",
        scope=(
            "Implement handoffs using context-pack.json and handoff-card.yaml "
            "schemas. Add code in agents/scripts/ for generating/validating "
            "handoff cards, integrate with new_task tool, and emit events on "
            "delegation."
        ),
        completion_signal=(
            "Use attempt_completion with a result summarizing handoff "
            "implementation (files updated, key functions like generate_handoff, "
            "tests passing), and deviations if any in docs/DEVIATIONS.md."
        ),
        parent_context=(
            "Parent Task Context: The overall goal is to review and implement "
            "a plan for standardizing agent context packs, handoff cards, and "
            "related improvements to reduce context drift and align agent work "
            "with project plans and DoD."
        ),
        dependencies=[
            "templates updated",
            "schemas defined",
            "Git MCP enabled",
        ],
        superseding_statement=(
            "These specific instructions supersede any conflicting general "
            "instructions in code mode."
        ),
    )
    print("Generated Handoff:")
    print(json.dumps(handoff, indent=2))
    print("\nFormatted for new_task tool:")
    print(format_for_new_task(handoff))
    print("\nEvent to emit:")
    print(json.dumps(emit_delegation_event(handoff)))
