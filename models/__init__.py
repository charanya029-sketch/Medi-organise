from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .patient import Patient
from .report import MedicalReport
from .laboratory import LaboratoryResult
from .history import MedicalHistory
from .summary import Summary

__all__ = ["db", "Patient", "MedicalReport", "LaboratoryResult", "MedicalHistory", "Summary"]
