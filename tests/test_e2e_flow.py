import io
import pytest
from app import create_app
from config import TestingConfig
from models import db, Patient, MedicalReport, LaboratoryResult, Summary

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_full_report_upload_verify_summary_flow(client, app):
    # 1. Intake Patient
    resp = client.post("/patients/add", data={
        "patient_id": "PT-E2E-TEST",
        "name": "Sarah Connor",
        "age": "39",
        "sex": "Female",
        "symptoms": "Occasional joint stiffness",
        "conditions": "Mild osteoarthritis",
        "allergies": "Aspirin",
        "medications": "Glucosamine 500mg"
    }, follow_redirects=True)
    assert resp.status_code == 200

    # 2. Upload Report using Sample Image
    sample_path = r"C:\Users\chara\.gemini\antigravity\scratch\medical-record-ai\static\images\sample_reports\sample_cbc_report.png"
    with open(sample_path, "rb") as f:
        file_bytes = f.read()

    upload_resp = client.post("/upload", data={
        "patient_id": "PT-E2E-TEST",
        "report_type": "Laboratory Report",
        "report_file": (io.BytesIO(file_bytes), "sample_cbc_report.png")
    }, content_type="multipart/form-data", follow_redirects=True)
    assert upload_resp.status_code == 200

    with app.app_context():
        rep = MedicalReport.query.filter_by(patient_id="PT-E2E-TEST").first()
        assert rep is not None
        assert rep.status == "PENDING_VERIFICATION"
        rep_id = rep.id

        # 3. Simulate user confirmation in verification interface
        labs = LaboratoryResult.query.filter_by(report_id=rep_id).all()
        confirm_data = {}
        for l in labs:
            prefix = f"lab_{l.id}_"
            confirm_data[f"{prefix}test_name"] = l.test_name
            confirm_data[f"{prefix}value"] = str(l.value)
            confirm_data[f"{prefix}unit"] = l.unit
            confirm_data[f"{prefix}reference_range"] = l.reference_range

    confirm_resp = client.post(f"/reports/confirm/{rep_id}", data=confirm_data, follow_redirects=True)
    assert confirm_resp.status_code == 200

    with app.app_context():
        rep = db.session.get(MedicalReport, rep_id)
        assert rep.status == "VERIFIED"

    # 4. Generate AI Summary
    summary_resp = client.post("/patients/PT-E2E-TEST/summarize", follow_redirects=True)
    assert summary_resp.status_code == 200

    with app.app_context():
        s = Summary.query.filter_by(patient_id="PT-E2E-TEST").first()
        assert s is not None
        assert "Sarah Connor" in s.summary_text
        assert "Medical Disclaimer" in s.summary_text
