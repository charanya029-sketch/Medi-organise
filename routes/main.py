from flask import Blueprint, render_template, request
from models import Patient, MedicalReport, LaboratoryResult, db

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("index.html")

@main_bp.route("/dashboard")
def dashboard():
    total_patients = Patient.query.count()
    total_reports = MedicalReport.query.count()
    total_lab_results = LaboratoryResult.query.count()

    recent_patients = Patient.query.order_by(Patient.created_at.desc()).limit(5).all()
    recent_reports = MedicalReport.query.order_by(MedicalReport.created_at.desc()).limit(5).all()

    # Search query
    q = request.args.get("q", "").strip()
    search_results = []
    if q:
        search_results = Patient.query.filter(
            (Patient.patient_id.ilike(f"%{q}%")) | (Patient.name.ilike(f"%{q}%"))
        ).all()

    return render_template(
        "dashboard.html",
        total_patients=total_patients,
        total_reports=total_reports,
        total_lab_results=total_lab_results,
        recent_patients=recent_patients,
        recent_reports=recent_reports,
        search_query=q,
        search_results=search_results
    )
