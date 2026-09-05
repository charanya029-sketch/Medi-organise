import re

def parse_reference_range(range_str):
    """
    Parses reference ranges strictly provided in the source report.
    Returns (lower_limit, upper_limit).
    Formats supported:
      - "12.0 - 16.0" -> (12.0, 16.0)
      - "70-99"       -> (70.0, 99.0)
      - "< 200"       -> (None, 200.0)
      - "<= 100"      -> (None, 100.0)
      - "> 60"        -> (60.0, None)
      - ">= 90"       -> (90.0, None)
    If no valid range or "Not provided", returns (None, None).
    """
    if not range_str or range_str.strip().lower() in ("not provided", "none", "n/a", ""):
        return None, None

    clean = range_str.strip()

    # Pattern: < or <= value
    m_less = re.search(r"^[<≤]=?\s*(-?\d+(?:\.\d+)?)$", clean)
    if m_less:
        return None, float(m_less.group(1))

    # Pattern: > or >= value
    m_greater = re.search(r"^[>≥]=?\s*(-?\d+(?:\.\d+)?)$", clean)
    if m_greater:
        return float(m_greater.group(1)), None

    # Pattern: lower - upper (handles hyphen, en-dash, em-dash, "to")
    m_range = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*(-?\d+(?:\.\d+)?)", clean)
    if m_range:
        try:
            low = float(m_range.group(1))
            high = float(m_range.group(2))
            return low, high
        except ValueError:
            pass

    return None, None

def evaluate_laboratory_value(value, reference_range_str, ocr_confidence=100.0):
    """
    Strict rule-based evaluation of laboratory values ONLY against source report reference ranges.
    
    Rules:
    - value < lower_limit -> LOW
    - lower_limit <= value <= upper_limit -> NORMAL
    - value > upper_limit -> HIGH
    - No reference range -> Reference Range: "Not provided", Status: "Not determined"
    - Anomaly / Low Confidence -> Status: "Needs verification"
    
    NEVER uses external reference ranges or AI judgment.
    NEVER silently modifies numeric values.
    """
    if value is None:
        return {
            "status": "Not determined",
            "reference_range": reference_range_str or "Not provided",
            "lower_limit": None,
            "upper_limit": None,
            "verification_required": True,
            "confidence": "Low",
            "notes": "Missing or non-numeric value"
        }

    lower_limit, upper_limit = parse_reference_range(reference_range_str)
    
    # If no reference range in source report
    if lower_limit is None and upper_limit is None:
        return {
            "status": "Not determined",
            "reference_range": "Not provided",
            "lower_limit": None,
            "upper_limit": None,
            "verification_required": False,
            "confidence": "High" if ocr_confidence >= 75 else ("Medium" if ocr_confidence >= 50 else "Low"),
            "notes": "No reference range provided in report"
        }

    # Rule-based comparison
    status = "NORMAL"
    if lower_limit is not None and upper_limit is not None:
        if value < lower_limit:
            status = "LOW"
        elif value > upper_limit:
            status = "HIGH"
        else:
            status = "NORMAL"
    elif upper_limit is not None:
        if value > upper_limit:
            status = "HIGH"
        else:
            status = "NORMAL"
    elif lower_limit is not None:
        if value < lower_limit:
            status = "LOW"
        else:
            status = "NORMAL"

    # Verification checks (Section 11)
    verification_required = False
    notes = ""

    # Low OCR confidence flag
    if ocr_confidence < 60.0:
        verification_required = True
        status = "Needs verification"
        notes = f"Low OCR confidence ({ocr_confidence}%)"

    # Check suspicious tenfold discrepancy (e.g. Creatinine 13 mg/dL vs normal 0.6-1.2)
    elif upper_limit is not None and upper_limit > 0 and (value >= upper_limit * 8):
        verification_required = True
        status = "Needs verification"
        notes = "Value significantly exceeds upper limit; requires human verification against report"
    elif lower_limit is not None and lower_limit > 0 and (value <= lower_limit / 8):
        verification_required = True
        status = "Needs verification"
        notes = "Value significantly below lower limit; requires human verification against report"

    confidence_label = "High" if ocr_confidence >= 75 else ("Medium" if ocr_confidence >= 50 else "Low")

    return {
        "status": status,
        "reference_range": reference_range_str,
        "lower_limit": lower_limit,
        "upper_limit": upper_limit,
        "verification_required": verification_required,
        "confidence": confidence_label,
        "notes": notes
    }

def validate_structured_report(structured_data, ocr_confidence=85.0):
    """
    Validates all laboratory items within structured report data and updates status.
    """
    validated_labs = []
    for lab in structured_data.get("laboratory_results", []):
        eval_res = evaluate_laboratory_value(
            lab.get("value"),
            lab.get("reference_range"),
            ocr_confidence=ocr_confidence
        )
        validated_labs.append({
            "test_name": lab.get("test_name"),
            "value": lab.get("value"),
            "raw_value_str": lab.get("raw_value_str") or str(lab.get("value")),
            "unit": lab.get("unit") or "",
            "reference_range": eval_res["reference_range"],
            "lower_limit": eval_res["lower_limit"],
            "upper_limit": eval_res["upper_limit"],
            "status": eval_res["status"],
            "confidence": eval_res["confidence"],
            "verification_required": eval_res["verification_required"],
            "source": lab.get("source", "EXTRACTED_FROM_REPORT")
        })

    return {
        **structured_data,
        "laboratory_results": validated_labs
    }
