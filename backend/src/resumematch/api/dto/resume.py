from pydantic import BaseModel, ConfigDict


class ExtractionResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    extraction_ok: bool
    page_count: int
    warnings: tuple[str, ...] = ()
