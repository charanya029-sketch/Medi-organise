from datetime import datetime, timezone
from . import db

class MedicalReport(db.Model):
    __tablename__ = "medical_reports"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(64), db.ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    report_type = db.Column(db.String(64), default="Laboratory Report")  # e.g., Laboratory Report, Prescription, Clinical Note
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    preprocessed_path = db.Column(db.String(512), nullable=True)
    report_date = db.Column(db.String(64), nullable=True)
    raw_ocr_text = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), default="PENDING_VERIFICATION")  # PENDING_VERIFICATION, VERIFIED
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    lab_results = db.relationship("LaboratoryResult", backref="report", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "report_type": self.report_type,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "preprocessed_path": self.preprocessed_path,
            "report_date": self.report_date,
            "raw_ocr_text": self.raw_ocr_text,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "lab_count": len(self.lab_results),
        }
