from pydantic import BaseModel


class TenantContext(BaseModel):
    id: str | None = None
    rate_limit_rps: int = 5
    model_caps: dict = {}
