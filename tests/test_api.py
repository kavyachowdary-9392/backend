from fastapi.testclient import TestClient

from app.extractor import ExtractionProviderError, normalize_draft
from app.main import app, get_extractor
from app.models import ExtractionDraft
from tests.sample_data import SAMPLE_CASES


class FakeExtractor:
    def extract(self, text: str):
        sample = next(item for item in SAMPLE_CASES if item["input"] == text)
        return normalize_draft(ExtractionDraft.model_validate(sample["draft"]), text)


def test_extract_endpoint_returns_all_required_fields_and_review_boolean():
    app.dependency_overrides[get_extractor] = FakeExtractor
    try:
        with TestClient(app) as client:
            response = client.post("/extract", json={"text": SAMPLE_CASES[0]["input"]})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"review_required", "fields"}
    assert set(body["fields"]) == {
        "vendor_name", "amount", "currency", "date", "category", "description", "invoice_id"
    }
    assert body["review_required"] is False


def test_all_five_assessment_inputs_complete_without_server_errors():
    app.dependency_overrides[get_extractor] = FakeExtractor
    try:
        with TestClient(app) as client:
            responses = [client.post("/extract", json={"text": item["input"]}) for item in SAMPLE_CASES]
    finally:
        app.dependency_overrides.clear()

    assert all(response.status_code == 200 for response in responses)
    assert responses[4].json()["review_required"] is True
    assert all(field["value"] is None for field in responses[4].json()["fields"].values())


def test_invalid_request_is_rejected():
    app.dependency_overrides[get_extractor] = FakeExtractor
    try:
        with TestClient(app) as client:
            response = client.post("/extract", json={"text": "ok", "extra": "not accepted"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 422


def test_provider_error_is_returned_as_gateway_error():
    class BrokenExtractor:
        def extract(self, _text: str):
            assert _text
            raise ExtractionProviderError("private provider details")

    app.dependency_overrides[get_extractor] = BrokenExtractor
    try:
        with TestClient(app) as client:
            response = client.post("/extract", json={"text": "some receipt"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert "private provider details" not in response.text
