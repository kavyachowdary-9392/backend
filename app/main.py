from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException

from app.extractor import (
    ExtractionProviderError,
    Extractor,
    create_extractor,
)
from app.models import ExtractRequest, ExtractionResponse

load_dotenv()

app = FastAPI(
    title="Structured Data Extractor",
    description="Extracts transaction fields from unstructured text with per-field confidence.",
    version="1.0.0",
)


@lru_cache(maxsize=1)
def get_extractor() -> Extractor:
    try:
        return create_extractor()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/", tags=["system"], include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "Structured Data Extractor is running. Use POST /extract or visit /docs.",
    }


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/extract", response_model=ExtractionResponse, tags=["extraction"])
def extract(
    request: ExtractRequest,
    extractor: Annotated[Extractor, Depends(get_extractor)],
) -> ExtractionResponse:
    try:
        return extractor.extract(request.text)
    except ExtractionProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail="The extraction provider failed to return a valid result.",
        ) from exc
