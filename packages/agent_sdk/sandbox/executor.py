from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ExecutionResult(BaseModel):
    """Result of code execution in sandbox."""

    exit_code: int = Field(..., description="Process exit code")
    stdout: str = Field(..., description="Standard output")
    stderr: str = Field(..., description="Standard error")
    timed_out: bool = Field(False, description="Whether execution timed out")
    execution_time: float = Field(..., description="Execution time in seconds")
    memory_used: Optional[int] = Field(None, description="Memory used in MB")
    artifacts: Dict[str, Any] = Field(
        default_factory=dict, description="Generated artifacts"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When execution completed"
    )


class SandboxExecutor(ABC):
    """Abstract base class for sandbox code execution."""

    @abstractmethod
    async def execute(
        self,
        code: str,
        language: str,
        timeout: int = 30,
        mem_mb: int = 512,
        working_dir: Optional[str] = None,
    ) -> ExecutionResult:
        """Execute code in a sandboxed environment."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up any resources used by the executor."""
        pass

    def get_supported_languages(self) -> list[str]:
        """Get list of supported programming languages."""
        return ["python", "bash", "javascript", "typescript"]
