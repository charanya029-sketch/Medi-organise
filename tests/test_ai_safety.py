from services.ai_service import generate_patient_summary, structure_report_with_ai, AI_SUMMARY_SYSTEM_PROMPT, AI_STRUCTURING_SYSTEM_PROMPT

def test_system_prompt_safety_constraints():
    """Verify that system prompts contain explicit prohibitions against diagnosis and prescribing."""
    assert "Do NOT diagnose" in AI_SUMMARY_SYSTEM_PROMPT
    assert "Do NOT predict diseases" in AI_SUMMARY_SYSTEM_PROMPT
    assert "Do NOT recommend treatments" in AI_SUMMARY_SYSTEM_PROMPT
    assert "Do NOT recommend or prescribe medications" in AI_SUMMARY_SYSTEM_PROMPT
    assert "Do NOT provide medical advice" in AI_SUMMARY_SYSTEM_PROMPT

    assert "DO NOT invent" in AI_STRUCTURING_SYSTEM_PROMPT
    assert "DO NOT provide medical diagnosis" in AI_STRUCTURING_SYSTEM_PROMPT

def test_deterministic_summary_safety_and_provenance():
    """Verify generated summary adheres to provenance tracking and disclaimer rules."""
    patient = {
        "patient_id": "PT-SAFE-01",
        "name": "David Miller",
        "age": 52,
        "sex": "Male",
        "conditions": "Hyperlipidemia",
        "medications": "Atorvastatin 20mg",
        "allergies": "Codeine",
        "symptoms": "Mild fatigue"
    }

    lab_results = [
        {
            "test_name": "Hemoglobin",
            "value": 10.2,
            "unit": "g/dL",
            "reference_range": "12.0 - 16.0",
            "status": "LOW",
            "source": "EXTRACTED_FROM_REPORT"
        },
        {
            "test_name": "Glucose",
            "value": 92.0,
            "unit": "mg/dL",
            "reference_range": "70 - 99",
            "status": "NORMAL",
            "source": "EXTRACTED_FROM_REPORT"
        }
    ]

    histories = []

    res = generate_patient_summary(patient, lab_results, histories)
    summary_text = res["summary_text"]

    # Verify Provenance markers
    assert "Source: User Provided" in summary_text
    assert "Source: Extracted from Report" in summary_text

    # Verify findings are strictly grouped by report range
    assert "Hemoglobin: 10.2 g/dL" in summary_text
    assert "Glucose: 92.0 mg/dL" in summary_text

    # Verify Medical Disclaimer is present
    assert "Medical Disclaimer" in summary_text
    assert "does not provide medical diagnosis" in summary_text.lower()
