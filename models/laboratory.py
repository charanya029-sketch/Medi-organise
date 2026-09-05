from datetime import datetime, timezone
from . import db

class LaboratoryResult(db.Model):
    __tablename__ = "laboratory_results"

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey("medical_reports.id", ondelete="CASCADE"), nullable=True, index=True)
    patient_id = db.Column(db.String(64), db.ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    test_name = db.Column(db.String(128), nullable=False)
    value = db.Column(db.Float, nullable=True)
    raw_value_str = db.Column(db.String(64), nullable=True)  # Preserves exact OCR string e.g. "10.2", "< 0.5"
    unit = db.Column(db.String(64), nullable=True)
    reference_range = db.Column(db.String(128), nullable=True)  # Strictly from report or "Not provided"
    lower_limit = db.Column(db.Float, nullable=True)
    upper_limit = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(32), default="Not determined")  # LOW, NORMAL, HIGH, Not determined, Needs verification
    confidence = db.Column(db.String(32), default="High")  # High, Medium, Low
    verification_required = db.Column(db.Boolean, default=False)
    user_verified = db.Column(db.Boolean, default=False)
    user_corrected = db.Column(db.Boolean, default=False)
    source = db.Column(db.String(64), default="EXTRACTED_FROM_REPORT")  # EXTRACTED_FROM_REPORT, USER_PROVIDED, USER_VERIFIED, USER_CORRECTED
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "report_id": self.report_id,
            "patient_id": self.patient_id,
            "test_name": self.test_name,
            "value": self.value,
            "raw_value_str": self.raw_value_str,
            "unit": self.unit or "",
            "reference_range": self.reference_range or "Not provided",
            "lower_limit": self.lower_limit,
            "upper_limit": self.upper_limit,
            "status": self.status,
            "confidence": self.confidence,
            "verification_required": self.verification_required,
            "user_verified": self.user_verified,
            "user_corrected": self.user_corrected,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
