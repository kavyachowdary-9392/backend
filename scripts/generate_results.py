"""Generate the assessment artifact through the same FastAPI endpoint used in production.

The fixtures stand in for Gemini only because this workspace has no API credential.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.extractor import normalize_draft
from app.main import app, get_extractor
from app.models import ExtractionDraft
from tests.sample_data import SAMPLE_CASES


class FixtureExtractor:
    def __init__(self) -> None:
        self._drafts = iter(SAMPLE_CASES)

    def extract(self, text: str):
        sample = next(self._drafts)
        if text != sample["input"]:
            raise AssertionError("Sample request order or text does not match the assessment")
        return normalize_draft(ExtractionDraft.model_validate(sample["draft"]), text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate sample extraction results.")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Call the configured Gemini model instead of deterministic test fixtures.",
    )
    args = parser.parse_args()

    if not args.live:
        fixture_extractor = FixtureExtractor()
        app.dependency_overrides[get_extractor] = lambda: fixture_extractor
    try:
        with TestClient(app) as client:
            results = []
            for sample in SAMPLE_CASES:
                response = client.post("/extract", json={"text": sample["input"]})
                response.raise_for_status()
                results.append(response.json())
        output = ROOT / "results.json"
        output.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {len(results)} endpoint responses to {output}")
    finally:
        if not args.live:
            app.dependency_overrides.clear()


if __name__ == "__main__":
    main()
