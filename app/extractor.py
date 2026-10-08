from __future__ import annotations

import math
import os
import re
from datetime import date, datetime
from typing import Protocol

from google import genai
from google.genai import types

from app.models import (
    CandidateAmount,
    CandidateString,
    ExtractionDraft,
    ExtractionResponse,
    FieldResult,
)
from app.prompts import build_prompt

REVIEW_THRESHOLD = 0.75
CATEGORIES = {"food", "travel", "utilities", "software", "other"}
FIELD_NAMES = (
    "vendor_name",
    "amount",
    "currency",
    "date",
    "category",
    "description",
    "invoice_id",
)


class ExtractionProviderError(RuntimeError):
    """Raised when the configured LLM cannot return a usable extraction."""


class Extractor(Protocol):
    def extract(self, text: str) -> ExtractionResponse: ...


class GeminiExtractor:
    def __init__(self, api_key: str, model: str = "gemini-3.5-flash-lite") -> None:
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def extract(self, text: str) -> ExtractionResponse:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=build_prompt(text, date.today()),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ExtractionDraft,
                    temperature=0.1,
                ),
            )
            parsed = response.parsed
            if isinstance(parsed, ExtractionDraft):
                draft = parsed
            elif parsed is not None:
                draft = ExtractionDraft.model_validate(parsed)
            elif response.text:
                draft = ExtractionDraft.model_validate_json(response.text)
            else:
                raise ValueError("The model returned an empty response")
        except Exception as exc:
            raise ExtractionProviderError("The extraction model did not return valid data") from exc

        return normalize_draft(draft, text)


def _confidence(candidate: CandidateString | CandidateAmount) -> float:
    try:
        value = float(candidate.confidence)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(value):
        return 0.0
    return max(0.0, min(1.0, value))


def _string_value(candidate: CandidateString, max_length: int = 500) -> str | None:
    if candidate.value is None:
        return None
    value = " ".join(candidate.value.strip().split())
    return value[:max_length] or None


def _amount_value(candidate: CandidateAmount) -> float | None:
    value = candidate.value
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, str):
        cleaned = re.sub(r"[^0-9.\-]", "", value.replace(",", ""))
        if not cleaned or cleaned in {".", "-", "-."}:
            return None
        value = cleaned
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return None
    return amount if math.isfinite(amount) else None


def _normalise_date(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        pass
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _source_supports_date(value: str, source_text: str) -> bool:
    """Reject model-invented days when the source only provides a month and year."""
    if not source_text:
        return True
    parsed = date.fromisoformat(value)
    if parsed.isoformat() in source_text:
        return True

    for match in re.finditer(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b", source_text):
        for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                if datetime.strptime(match.group(), fmt).date() == parsed:
                    return True
            except ValueError:
                continue
    month_names = {
        1: "January|Jan", 2: "February|Feb", 3: "March|Mar", 4: "April|Apr",
        5: "May", 6: "June|Jun", 7: "July|Jul", 8: "August|Aug",
        9: "September|Sep|Sept", 10: "October|Oct", 11: "November|Nov",
        12: "December|Dec",
    }[parsed.month]
    day = rf"0?{parsed.day}(?:st|nd|rd|th)?"
    complete_named_date = re.search(
        rf"\b(?:{month_names})\s+{day}[,]?\s+{parsed.year}\b|"
        rf"\b{day}\s+(?:{month_names})[,]?\s+{parsed.year}\b",
        source_text,
        re.IGNORECASE,
    )
    if complete_named_date:
        return True

    partial_month_year = re.search(
        rf"\b(?:{month_names})\s+{parsed.year}\b|\b{parsed.year}\s+(?:{month_names})\b",
        source_text,
        re.IGNORECASE,
    )
    return partial_month_year is None


def _source_supports_invoice_id(value: str, source_text: str) -> bool:
    """Only accept identifiers explicitly presented as invoice/reference numbers."""
    if not source_text:
        return True
    position = source_text.casefold().find(value.casefold())
    if position < 0:
        return False
    if re.match(r"INV[-_/]", value, re.IGNORECASE):
        return True
    preceding_text = source_text[max(0, position - 60) : position]
    return re.search(r"\b(?:invoice|reference|ref)\b", preceding_text, re.IGNORECASE) is not None


def _result(value: str | float | None, confidence: float) -> FieldResult:
    # A null cannot be treated as a confident, auto-saveable extraction.
    if value is None:
        confidence = min(confidence, 0.20)
    confidence = round(max(0.0, min(1.0, confidence)), 4)
    return FieldResult(
        value=value,
        confidence=confidence,
        needs_review=confidence < REVIEW_THRESHOLD,
    )


def normalize_draft(draft: ExtractionDraft, source_text: str = "") -> ExtractionResponse:
    """Validate model values and compute review flags on the server."""
    fields: dict[str, FieldResult] = {}

    for name in FIELD_NAMES:
        candidate = getattr(draft, name)
        confidence = _confidence(candidate)

        if name == "amount":
            value: str | float | None = _amount_value(candidate)
            if value is not None and re.search(
                r"\b(?:like|about|around|roughly|approximately|approx\.)\b",
                source_text,
                re.IGNORECASE,
            ):
                confidence = min(confidence, 0.70)
        else:
            value = _string_value(candidate)
            if name == "currency" and value is not None:
                value = value.upper()
                if not re.fullmatch(r"[A-Z]{3}", value):
                    value = None
            elif name == "date":
                value = _normalise_date(value)
                if value is not None and not _source_supports_date(value, source_text):
                    value = None
            elif name == "category" and value is not None:
                value = value.lower()
                if value not in CATEGORIES:
                    value = None
            elif name == "description" and value is not None:
                value = value.replace("\n", " ")
            elif name == "invoice_id" and value is not None:
                if not _source_supports_invoice_id(value, source_text):
                    value = None

        if value is None:
            confidence = min(confidence, 0.20)
        fields[name] = _result(value, confidence)

    return ExtractionResponse(
        review_required=any(field.needs_review for field in fields.values()),
        fields=fields,
    )


def create_extractor() -> GeminiExtractor:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    return GeminiExtractor(
        api_key=api_key,
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
    )
