import pytest
from datetime import datetime, timezone, timedelta
from app import create_app
from config import TestingConfig
from models import db, Patient, MedicalReport, LaboratoryResult

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

def test_patient_specific_test_history(client, app):
    with app.app_context():
        p1 = Patient(patient_id="PT-HIST-01", name="History Patient 1")
        p2 = Patient(patient_id="PT-HIST-02", name="History Patient 2")
        db.session.add_all([p1, p2])
        db.session.commit()

        # Add multiple glucose tests across different dates
        t1 = LaboratoryResult(
            patient_id="PT-HIST-01",
            test_name="Glucose",
            value=95.0,
            unit="mg/dL",
            reference_range="70-99",
            status="NORMAL",
            created_at=datetime.now(timezone.utc) - timedelta(days=30)
        )
        t2 = LaboratoryResult(
            patient_id="PT-HIST-01",
            test_name="Glucose",
            value=115.0,
            unit="mg/dL",
            reference_range="70-99",
            status="HIGH",
            created_at=datetime.now(timezone.utc)
        )
        t3 = LaboratoryResult(
            patient_id="PT-HIST-02",
            test_name="Glucose",
            value=88.0,
            unit="mg/dL",
            reference_range="70-99",
            status="NORMAL",
            created_at=datetime.now(timezone.utc)
        )
        db.session.add_all([t1, t2, t3])
        db.session.commit()

    # Query for PT-HIST-01's history
    resp = client.get("/patients/PT-HIST-01/history?test=Glucose")
    assert resp.status_code == 200
    assert b"History Patient 1" in resp.data
    assert b"115.0" in resp.data
    assert b"95.0" in resp.data
    # Should NOT contain Patient 2's value
    assert b"88.0" not in resp.data
