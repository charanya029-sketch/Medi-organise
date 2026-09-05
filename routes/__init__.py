# Routes package
from .main import main_bp
from .patients import patients_bp
from .reports import reports_bp
from .api import api_bp

__all__ = ["main_bp", "patients_bp", "reports_bp", "api_bp"]
