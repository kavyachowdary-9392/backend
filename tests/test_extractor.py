from app.extractor import normalize_draft
from app.models import ExtractionDraft


def _valid_draft(**overrides):
    fields = {
        "vendor_name": {"value": "Acme", "confidence": 0.9},
        "amount": {"value": 42, "confidence": 0.9},
        "currency": {"value": "inr", "confidence": 0.9},
        "date": {"value": "29-04-2024", "confidence": 0.9},
        "category": {"value": "travel", "confidence": 0.9},
        "description": {"value": "A ride", "confidence": 0.9},
        "invoice_id": {"value": "REF-42", "confidence": 0.9},
    }
    fields.update(overrides)
    return ExtractionDraft.model_validate(fields)


def test_normalizes_fields_and_emits_exact_review_flags():
    result = normalize_draft(_valid_draft(amount={"value": "₹ 1,250.50", "confidence": 0.9}))

    assert result.fields.amount.value == 1250.5
    assert result.fields.currency.value == "INR"
    assert result.fields.date.value == "2024-04-29"
    assert result.review_required is False
    assert all(not field["needs_review"] for field in result.fields.model_dump().values())


def test_confidence_below_threshold_requires_review():
    result = normalize_draft(_valid_draft(amount={"value": 42, "confidence": 0.749}))

    assert result.fields.amount.needs_review is True
    assert result.review_required is True


def test_missing_or_invalid_values_are_null_and_low_confidence():
    result = normalize_draft(
        _valid_draft(
            vendor_name={"value": None, "confidence": 0.99},
            date={"value": "April 2024", "confidence": 0.8},
            category={"value": "shopping", "confidence": 0.9},
        )
    )

    assert result.fields.vendor_name.value is None
    assert result.fields.vendor_name.confidence == 0.2
    assert result.fields.date.value is None
    assert result.fields.date.needs_review is True
    assert result.fields.category.value is None
    assert result.review_required is True


def test_non_finite_confidence_is_safely_clamped():
    result = normalize_draft(_valid_draft(amount={"value": 42, "confidence": float("nan")}))

    assert result.fields.amount.confidence == 0.0
    assert result.fields.amount.needs_review is True


def test_month_only_date_is_not_promoted_to_first_of_month():
    result = normalize_draft(
        _valid_draft(date={"value": "2024-04-01", "confidence": 0.55}),
        "Zoho subscription, April 2024",
    )

    assert result.fields.date.value is None
    assert result.fields.date.needs_review is True


def test_transport_token_is_not_accepted_as_invoice_id():
    result = normalize_draft(
        _valid_draft(invoice_id={"value": "0042", "confidence": 0.9}),
        "DELHI METRO RAIL CORP Token: 0042 Fare: INR 30",
    )

    assert result.fields.invoice_id.value is None
    assert result.fields.invoice_id.needs_review is True


def test_approximate_amount_confidence_is_limited():
    result = normalize_draft(
        _valid_draft(amount={"value": 340, "confidence": 0.95}),
        "It was like 340 rupees",
    )

    assert result.fields.amount.confidence == 0.7
    assert result.fields.amount.needs_review is True
