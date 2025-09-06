from pydantic import BaseModel
class AgentContext(BaseModel):
    task: dict; tools: list; memory: dict; telemetry: dict; tenant_id: str|None=None
class AgentBase:
    def capabilities(self) -> list[str]: return []
    async def execute(self, ctx: AgentContext) -> dict: raise NotImplementedError