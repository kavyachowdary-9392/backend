from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ExtractRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(max_length=30_000, description="Unstructured transaction text")


class CandidateString(BaseModel):
    value: str | None = None
    confidence: float = 0.0


class CandidateAmount(BaseModel):
    value: float | str | None = None
    confidence: float = 0.0


class ExtractionDraft(BaseModel):
    """Untrusted, per-field extraction returned by the language model."""

    vendor_name: CandidateString = Field(default_factory=CandidateString)
    amount: CandidateAmount = Field(default_factory=CandidateAmount)
    currency: CandidateString = Field(default_factory=CandidateString)
    date: CandidateString = Field(default_factory=CandidateString)
    category: CandidateString = Field(default_factory=CandidateString)
    description: CandidateString = Field(default_factory=CandidateString)
    invoice_id: CandidateString = Field(default_factory=CandidateString)


class FieldResult(BaseModel):
    value: str | float | None
    confidence: float = Field(ge=0.0, le=1.0)
    needs_review: bool


class ExtractedFields(BaseModel):
    vendor_name: FieldResult
    amount: FieldResult
    currency: FieldResult
    date: FieldResult
    category: FieldResult
    description: FieldResult
    invoice_id: FieldResult


class ExtractionResponse(BaseModel):
    review_required: bool
    fields: ExtractedFields


Category = Literal["food", "travel", "utilities", "software", "other"]
