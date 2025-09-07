from pydantic import BaseModel


class ValidationResult(BaseModel):
    ok: bool
    findings: list[str] = []


class OutputValidator:
    async def validate_code(self, path: str) -> ValidationResult:
        return ValidationResult(ok=True)

    async def validate_against_dod(
        self, artifacts: list[dict], dod: list[str]
    ) -> ValidationResult:
        # naive DoD check
        have = " ".join([a.get("summary", "") for a in artifacts])
        missing = [d for d in dod if d not in have]
        return ValidationResult(
            ok=(len(missing) == 0), findings=[f"Missing DoD: {m}" for m in missing]
        )

    async def validate_security(self, path: str) -> ValidationResult:
        return ValidationResult(ok=True)
