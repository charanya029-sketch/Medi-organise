import pytest
from services.validation_service import evaluate_laboratory_value, parse_reference_range

def test_parse_reference_range():
    assert parse_reference_range("12.0 - 16.0") == (12.0, 16.0)
    assert parse_reference_range("70-99") == (70.0, 99.0)
    assert parse_reference_range("< 200") == (None, 200.0)
    assert parse_reference_range("> 60") == (60.0, None)
    assert parse_reference_range("Not provided") == (None, None)
    assert parse_reference_range("") == (None, None)

def test_rule_based_comparisons():
    # 1. LOW Value
    res_low = evaluate_laboratory_value(10.2, "12.0 - 16.0", ocr_confidence=95.0)
    assert res_low["status"] == "LOW"
    assert res_low["verification_required"] is False

    # 2. NORMAL Value
    res_norm = evaluate_laboratory_value(14.0, "12.0 - 16.0", ocr_confidence=95.0)
    assert res_norm["status"] == "NORMAL"
    assert res_norm["verification_required"] is False

    # 3. HIGH Value
    res_high = evaluate_laboratory_value(18.5, "12.0 - 16.0", ocr_confidence=95.0)
    assert res_high["status"] == "HIGH"
    assert res_high["verification_required"] is False

def test_missing_reference_range_status():
    """Verify that when no reference range is provided, status is strictly 'Not determined'."""
    res = evaluate_laboratory_value(14.5, "Not provided", ocr_confidence=90.0)
    assert res["status"] == "Not determined"
    assert res["reference_range"] == "Not provided"

def test_needs_verification_on_suspicious_outlier():
    """
    Creatinine 13 mg/dL with reference range 0.6 - 1.2:
    The system must NOT change it to 1.3 mg/dL.
    It MUST flag it as 'Needs verification'.
    """
    res = evaluate_laboratory_value(13.0, "0.6 - 1.2", ocr_confidence=88.0)
    assert res["status"] == "Needs verification"
    assert res["verification_required"] is True

def test_low_ocr_confidence_triggers_verification():
    """OCR confidence below 60% must flag for verification."""
    res = evaluate_laboratory_value(14.0, "12.0 - 16.0", ocr_confidence=45.0)
    assert res["status"] == "Needs verification"
    assert res["verification_required"] is True
