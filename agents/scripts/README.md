# Handoff Script

This script provides functions to generate and validate handoff cards based on the handoff-card.yaml schema. It formats the handoff for the new_task tool and prepares an event for delegation.

## Usage

### Generate Handoff Card

Use `generate_handoff` to create a handoff dict from parameters.

### Format for new_task Tool

Use `format_for_new_task` to get XML formatted for the new_task tool.

### Emit Delegation Event

Use `emit_delegation_event` to format the event JSON to be emitted via docs-emit-event.py.

### Example

Run `python handoff.py` to see a sample handoff from orchestrator to code mode, using a snippet from backend-current-plan.md. It generates the handoff, formats it for new_task, and shows the event to emit.

Example output:
- Generated Handoff: JSON dict
- Formatted for new_task tool: XML string
- Event to emit: JSON event

## Integration with new_task

The formatted XML from `format_for_new_task` can be used as the message for the new_task tool call.

## Unit Tests

Run `pytest test_handoff.py` to validate the functions.

## Dependencies

- yaml
- json
- jsonschema
- pytest (for tests)