import asyncio, tempfile, os, textwrap
from .executor import ExecutionResult, SandboxExecutor
class SubprocessSandbox(SandboxExecutor):
    async def execute(self, code, language, timeout=30, mem_mb=512):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, f"snippet.{ 'py' if language=='python' else 'sh'}")
            with open(path,"w") as f: f.write(textwrap.dedent(code))
            cmd = ["python", path] if language=="python" else ["bash", path]
            try:
                p = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=td)
                out, err = await asyncio.wait_for(p.communicate(), timeout=timeout)
                return ExecutionResult(exit_code=p.returncode, stdout=out.decode(), stderr=err.decode())
            except asyncio.TimeoutError:
                return ExecutionResult(exit_code=124, stdout="", stderr="Timed out", timed_out=True)