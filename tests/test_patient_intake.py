import pytest
from app import create_app
from config import TestingConfig
from models import db, Patient

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

def test_valid_patient_intake(client, app):
    """Test creating a patient with valid required and optional fields."""
    response = client.post("/patients/add", data={
        "patient_id": "PT-001",
        "name": "Alice Walker",
        "age": "34",
        "sex": "Female",
        "symptoms": "Occasional dizziness",
        "conditions": "Mild asthma",
        "allergies": "Sulfa drugs",
        "medications": "Albuterol inhaler",
        "additional_notes": "None"
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        p = Patient.query.filter_by(patient_id="PT-001").first()
        assert p is not None
        assert p.name == "Alice Walker"
        assert p.age == 34
        assert p.sex == "Female"
        assert p.allergies == "Sulfa drugs"

def test_missing_required_fields(client, app):
    """Test that missing patient_id or name fails validation."""
    response = client.post("/patients/add", data={
        "patient_id": "",
        "name": "No ID Patient"
    }, follow_redirects=True)
    assert b"Patient ID is required" in response.data

    response2 = client.post("/patients/add", data={
        "patient_id": "PT-NO-NAME",
        "name": ""
    }, follow_redirects=True)
    assert b"Patient Name is required" in response2.data

def test_duplicate_patient_id(client, app):
    """Test that registering an existing patient_id is rejected."""
    client.post("/patients/add", data={"patient_id": "PT-DUP", "name": "First Entry"})
    response = client.post("/patients/add", data={"patient_id": "PT-DUP", "name": "Second Entry"}, follow_redirects=True)
    assert b"already exists" in response.data

def test_invalid_age(client, app):
    """Test that non-numeric or out-of-range age is rejected."""
    response = client.post("/patients/add", data={
        "patient_id": "PT-BAD-AGE",
        "name": "Bad Age",
        "age": "999"
    }, follow_redirects=True)
    assert b"valid age" in response.data
