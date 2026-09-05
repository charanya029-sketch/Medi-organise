from services.extraction_service import extract_structured_data

def test_decimal_and_unit_extraction():
    sample_text = """
    Patient Name: John Doe
    Patient ID: PT-9901
    Report Date: 2026-04-15

    TEST NAME          VALUE    UNIT      REFERENCE RANGE
    Hemoglobin         10.2     g/dL      12.0 - 16.0
    Glucose            95.5     mg/dL     70 - 99
    Creatinine         1.3      mg/dL     0.6 - 1.2
    Platelets          250      10^3/uL   150 - 450
    """

    data = extract_structured_data(sample_text)

    assert data["patient_information"]["name"] == "John Doe"
    assert data["patient_information"]["patient_id"] == "PT-9901"
    assert data["report_date"] == "2026-04-15"

    labs = {l["test_name"]: l for l in data["laboratory_results"]}

    # Verify Hemoglobin decimal precision and unit
    assert "Hemoglobin" in labs
    assert labs["Hemoglobin"]["value"] == 10.2
    assert labs["Hemoglobin"]["unit"] == "g/dL"
    assert "12.0 - 16.0" in labs["Hemoglobin"]["reference_range"]

    # Verify Glucose decimal
    assert "Glucose" in labs
    assert labs["Glucose"]["value"] == 95.5
    assert labs["Glucose"]["unit"] == "mg/dL"

    # Verify Creatinine
    assert "Creatinine" in labs
    assert labs["Creatinine"]["value"] == 1.3
    assert labs["Creatinine"]["unit"] == "mg/dL"

def test_missing_reference_range():
    """Verify that when a reference range is absent from the report, it is set to 'Not provided'."""
    text = "Hemoglobin 14.5 g/dL"
    data = extract_structured_data(text)
    assert len(data["laboratory_results"]) == 1
    assert data["laboratory_results"][0]["reference_range"] == "Not provided"
