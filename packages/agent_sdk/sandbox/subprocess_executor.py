import asyncio
import os
import tempfile
import textwrap
import time

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover
    psutil = None  # type: ignore[assignment]
from typing import Optional

from .executor import ExecutionResult, SandboxExecutor


class SubprocessSandbox(SandboxExecutor):
    """Subprocess-based sandbox executor with timeout and resource limits."""

    def __init__(self, base_temp_dir: Optional[str] = None):
        self.base_temp_dir = base_temp_dir
        self._temp_dirs: list[str] = []

    async def execute(
        self,
        code: str,
        language: str,
        timeout: int = 30,
        mem_mb: int = 512,
        working_dir: Optional[str] = None,
    ) -> ExecutionResult:
        """Execute code in a subprocess with timeout and memory limits."""
        start_time = time.time()
        temp_dir = None

        try:
            # Create temporary directory
            if working_dir:
                temp_dir = working_dir
            else:
                temp_dir = tempfile.mkdtemp(dir=self.base_temp_dir)
                self._temp_dirs.append(temp_dir)

            # Determine file extension and command
            file_ext, cmd = self._get_language_config(language)
            if not file_ext or not cmd:
                return ExecutionResult(
                    exit_code=1,
                    stdout="",
                    stderr=f"Unsupported language: {language}",
                    execution_time=time.time() - start_time,
                    timed_out=False,
                    memory_used=0,
                )

            # Write code to file
            file_path = os.path.join(temp_dir, f"snippet.{file_ext}")
            with open(file_path, "w") as f:
                f.write(textwrap.dedent(code))

            # Set up process with resource limits
            process = await asyncio.create_subprocess_exec(
                *cmd,
                file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=temp_dir,
                preexec_fn=(
                    self._set_resource_limits(mem_mb) if os.name != "nt" else None
                ),
            )

            try:
                # Wait for completion with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )

                execution_time = time.time() - start_time

                # Get memory usage if possible
                memory_used = 0
                try:
                    if process.returncode is not None:
                        memory_used = self._get_memory_usage(process.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    memory_used = 0

                return ExecutionResult(
                    exit_code=process.returncode or 0,
                    stdout=stdout.decode("utf-8", errors="replace"),
                    stderr=stderr.decode("utf-8", errors="replace"),
                    execution_time=execution_time,
                    timed_out=False,
                    memory_used=memory_used,
                )

            except asyncio.TimeoutError:
                # Kill the process if it times out
                try:
                    process.kill()
                    await process.wait()
                except ProcessLookupError:
                    pass

                execution_time = time.time() - start_time
                return ExecutionResult(
                    exit_code=124,
                    stdout="",
                    stderr="Execution timed out",
                    timed_out=True,
                    execution_time=execution_time,
                    memory_used=0,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                execution_time=execution_time,
                timed_out=False,
                memory_used=0,
            )

    def _get_language_config(
        self, language: str
    ) -> tuple[Optional[str], Optional[list[str]]]:
        """Get file extension and command for language."""
        configs = {
            "python": (".py", ["python", "-u"]),
            "bash": (".sh", ["bash"]),
            "sh": (".sh", ["bash"]),
            "javascript": (".js", ["node"]),
            "typescript": (".ts", ["ts-node"]),
        }
        return configs.get(language.lower(), (None, None))

    def _set_resource_limits(self, mem_mb: int):
        """Set resource limits for the subprocess."""

        def set_limits():
            import resource

            # Set memory limit
            mem_bytes = mem_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))

        return set_limits

    def _get_memory_usage(self, pid: int) -> int:
        """Get memory usage in MB for a process."""
        try:
            process = psutil.Process(pid)
            memory_info = process.memory_info()
            rss_bytes: int = memory_info.rss
            return rss_bytes // (1024 * 1024)  # Convert to MB
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0

    async def cleanup(self) -> None:
        """Clean up temporary directories."""
        for temp_dir in self._temp_dirs:
            try:
                import shutil

                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
        self._temp_dirs.clear()

    def get_supported_languages(self) -> list[str]:
        """Get list of supported programming languages."""
        return ["python", "bash", "sh", "javascript", "typescript"]
