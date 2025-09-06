class CapabilityNegotiator:
    def match(self, task: dict, agents: list) -> tuple[object, list[str]]:
        # naive: return first agent; later: check task.labels vs agent.capabilities()
        return (agents[0] if agents else None, [])