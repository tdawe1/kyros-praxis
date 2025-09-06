from pydantic import BaseModel
class ExecutionResult(BaseModel):
    exit_code: int; stdout: str; stderr: str; timed_out: bool=False
class SandboxExecutor:
    async def execute(self, code:str, language:str, timeout:int=30, mem_mb:int=512) -> ExecutionResult: ...