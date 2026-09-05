from datetime import datetime, timezone
from . import db

class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    sex = db.Column(db.String(16), nullable=True)
    symptoms = db.Column(db.Text, nullable=True)
    conditions = db.Column(db.Text, nullable=True)
    allergies = db.Column(db.Text, nullable=True)
    medications = db.Column(db.Text, nullable=True)
    additional_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    reports = db.relationship("MedicalReport", backref="patient", lazy=True, cascade="all, delete-orphan")
    lab_results = db.relationship("LaboratoryResult", backref="patient", lazy=True, cascade="all, delete-orphan")
    histories = db.relationship("MedicalHistory", backref="patient", lazy=True, cascade="all, delete-orphan")
    summaries = db.relationship("Summary", backref="patient", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "name": self.name,
            "age": self.age,
            "sex": self.sex,
            "symptoms": self.symptoms,
            "conditions": self.conditions,
            "allergies": self.allergies,
            "medications": self.medications,
            "additional_notes": self.additional_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "total_reports": len(self.reports),
            "total_lab_results": len(self.lab_results),
        }
