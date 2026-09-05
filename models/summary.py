from datetime import datetime, timezone
from . import db

class Summary(db.Model):
    __tablename__ = "summaries"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(64), db.ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    summary_text = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(64), default="AI_GENERATED")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "summary_text": self.summary_text,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
