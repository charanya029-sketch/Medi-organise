from datetime import datetime, timezone
from . import db

class MedicalHistory(db.Model):
    __tablename__ = "medical_histories"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(64), db.ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    category = db.Column(db.String(64), nullable=False)  # Symptom, Condition, Allergy, Medication, Clinical Note
    information = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(64), default="USER_PROVIDED")  # USER_PROVIDED, EXTRACTED_FROM_REPORT
    date = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "category": self.category,
            "information": self.information,
            "source": self.source,
            "date": self.date,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
