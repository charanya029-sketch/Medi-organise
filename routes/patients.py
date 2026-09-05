from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, Patient, MedicalReport, LaboratoryResult, MedicalHistory, Summary
from services.ai_service import generate_patient_summary

patients_bp = Blueprint("patients", __name__, url_prefix="/patients")

@patients_bp.route("/", strict_slashes=False)
def list_patients():
    q = request.args.get("q", "").strip()
    if q:
        patients = Patient.query.filter(
            (Patient.patient_id.ilike(f"%{q}%")) | (Patient.name.ilike(f"%{q}%"))
        ).order_by(Patient.created_at.desc()).all()
    else:
        patients = Patient.query.order_by(Patient.created_at.desc()).all()
    return render_template("patients.html", patients=patients, search_query=q)

@patients_bp.route("/add", methods=["GET", "POST"])
def add_patient():
    if request.method == "POST":
        patient_id = request.form.get("patient_id", "").strip()
        name = request.form.get("name", "").strip()
        age_str = request.form.get("age", "").strip()
        sex = request.form.get("sex", "").strip()
        symptoms = request.form.get("symptoms", "").strip()
        conditions = request.form.get("conditions", "").strip()
        allergies = request.form.get("allergies", "").strip()
        medications = request.form.get("medications", "").strip()
        additional_notes = request.form.get("additional_notes", "").strip()

        # Validation
        if not patient_id:
            flash("Patient ID is required.", "danger")
            return redirect(url_for("patients.list_patients"))
        if not name:
            flash("Patient Name is required.", "danger")
            return redirect(url_for("patients.list_patients"))

        existing = Patient.query.filter_by(patient_id=patient_id).first()
        if existing:
            flash(f"Patient with ID '{patient_id}' already exists.", "warning")
            return redirect(url_for("patients.list_patients"))

        age = None
        if age_str:
            try:
                age = int(age_str)
                if age < 0 or age > 150:
                    flash("Please enter a valid age between 0 and 150.", "danger")
                    return redirect(url_for("patients.list_patients"))
            except ValueError:
                flash("Age must be a valid number.", "danger")
                return redirect(url_for("patients.list_patients"))

        patient = Patient(
            patient_id=patient_id,
            name=name,
            age=age,
            sex=sex,
            symptoms=symptoms,
            conditions=conditions,
            allergies=allergies,
            medications=medications,
            additional_notes=additional_notes
        )
        db.session.add(patient)

        # Record intake items in MedicalHistory with source USER_PROVIDED
        if symptoms:
            db.session.add(MedicalHistory(patient_id=patient_id, category="Symptom", information=symptoms, source="USER_PROVIDED"))
        if conditions:
            db.session.add(MedicalHistory(patient_id=patient_id, category="Condition", information=conditions, source="USER_PROVIDED"))
        if allergies:
            db.session.add(MedicalHistory(patient_id=patient_id, category="Allergy", information=allergies, source="USER_PROVIDED"))
        if medications:
            db.session.add(MedicalHistory(patient_id=patient_id, category="Medication", information=medications, source="USER_PROVIDED"))
        if additional_notes:
            db.session.add(MedicalHistory(patient_id=patient_id, category="Note", information=additional_notes, source="USER_PROVIDED"))

        db.session.commit()
        flash(f"Patient '{name}' (ID: {patient_id}) created successfully.", "success")
        return redirect(url_for("patients.patient_profile", patient_id=patient_id))

    return render_template("patients.html")

@patients_bp.route("/<patient_id>")
def patient_profile(patient_id):
    patient = Patient.query.filter_by(patient_id=patient_id).first_or_404()
    
    # Reports sorted chronologically
    reports = MedicalReport.query.filter_by(patient_id=patient_id).order_by(MedicalReport.created_at.desc()).all()
    
    # Lab results
    test_filter = request.args.get("test_name", "").strip()
    status_filter = request.args.get("status", "").strip()
    
    lab_query = LaboratoryResult.query.filter_by(patient_id=patient_id)
    if test_filter:
        lab_query = lab_query.filter(LaboratoryResult.test_name.ilike(f"%{test_filter}%"))
    if status_filter:
        lab_query = lab_query.filter(LaboratoryResult.status == status_filter)
    
    lab_results = lab_query.order_by(LaboratoryResult.created_at.desc()).all()
    
    # Medical history entries
    histories = MedicalHistory.query.filter_by(patient_id=patient_id).order_by(MedicalHistory.created_at.desc()).all()
    
    # Latest AI summary
    latest_summary = Summary.query.filter_by(patient_id=patient_id).order_by(Summary.created_at.desc()).first()

    # Timeline construction
    timeline_events = _build_timeline_events(patient, reports, lab_results, histories)

    return render_template(
        "patient_profile.html",
        patient=patient,
        reports=reports,
        lab_results=lab_results,
        histories=histories,
        latest_summary=latest_summary,
        timeline_events=timeline_events,
        test_filter=test_filter,
        status_filter=status_filter
    )

@patients_bp.route("/<patient_id>/edit", methods=["POST"])
def edit_patient(patient_id):
    patient = Patient.query.filter_by(patient_id=patient_id).first_or_404()
    patient.name = request.form.get("name", patient.name).strip()
    age_str = request.form.get("age", "").strip()
    if age_str:
        try:
            patient.age = int(age_str)
        except ValueError:
            pass
    patient.sex = request.form.get("sex", patient.sex)
    patient.symptoms = request.form.get("symptoms", "").strip()
    patient.conditions = request.form.get("conditions", "").strip()
    patient.allergies = request.form.get("allergies", "").strip()
    patient.medications = request.form.get("medications", "").strip()
    patient.additional_notes = request.form.get("additional_notes", "").strip()
    
    db.session.commit()
    flash("Patient profile updated successfully.", "success")
    return redirect(url_for("patients.patient_profile", patient_id=patient_id))

@patients_bp.route("/<patient_id>/summarize", methods=["POST"])
def summarize_patient(patient_id):
    patient = Patient.query.filter_by(patient_id=patient_id).first_or_404()
    lab_results = LaboratoryResult.query.filter_by(patient_id=patient_id).all()
    histories = MedicalHistory.query.filter_by(patient_id=patient_id).all()

    patient_dict = patient.to_dict()
    labs_dict = [l.to_dict() for l in lab_results]
    histories_dict = [h.to_dict() for h in histories]

    res = generate_patient_summary(patient_dict, labs_dict, histories_dict)
    
    # Store summary in database
    new_summary = Summary(
        patient_id=patient_id,
        summary_text=res["summary_text"],
        source=res["source"]
    )
    db.session.add(new_summary)
    db.session.commit()

    flash("Patient summary successfully generated!", "success")
    return redirect(url_for("patients.patient_profile", patient_id=patient_id, _anchor="ai-summary"))

@patients_bp.route("/<patient_id>/history")
def patient_history(patient_id):
    patient = Patient.query.filter_by(patient_id=patient_id).first_or_404()
    
    test_query = request.args.get("test", "").strip()
    category_query = request.args.get("category", "").strip()
    
    lab_q = LaboratoryResult.query.filter_by(patient_id=patient_id)
    if test_query:
        lab_q = lab_q.filter(LaboratoryResult.test_name.ilike(f"%{test_query}%"))
    lab_results = lab_q.order_by(LaboratoryResult.created_at.desc()).all()

    hist_q = MedicalHistory.query.filter_by(patient_id=patient_id)
    if category_query:
        hist_q = hist_q.filter(MedicalHistory.category.ilike(f"%{category_query}%"))
    histories = hist_q.order_by(MedicalHistory.created_at.desc()).all()

    reports = MedicalReport.query.filter_by(patient_id=patient_id).order_by(MedicalReport.created_at.desc()).all()

    return render_template(
        "history.html",
        patient=patient,
        lab_results=lab_results,
        histories=histories,
        reports=reports,
        test_query=test_query,
        category_query=category_query
    )

def _build_timeline_events(patient, reports, lab_results, histories):
    events = []
    
    # Patient intake event
    if patient.created_at:
        events.append({
            "date": patient.created_at.strftime("%B %Y"),
            "exact_date": patient.created_at.strftime("%Y-%m-%d"),
            "title": "Patient Record Created",
            "type": "Patient Intake",
            "badge_class": "bg-primary",
            "description": f"Initial clinical intake recorded for {patient.name}. Symptoms and preexisting conditions documented.",
            "source": "USER_PROVIDED"
        })

    # Reports events
    for r in reports:
        dt_str = r.report_date or (r.created_at.strftime("%Y-%m-%d") if r.created_at else "Unknown Date")
        events.append({
            "date": r.created_at.strftime("%B %Y") if r.created_at else "Recent",
            "exact_date": dt_str,
            "title": f"Report Uploaded: {r.report_type}",
            "type": "Medical Report",
            "badge_class": "bg-info text-dark",
            "description": f"File: {r.file_name} ({len(r.lab_results)} lab tests extracted). Status: {r.status}.",
            "source": "EXTRACTED_FROM_REPORT",
            "report_id": r.id
        })

    # Sort events by exact_date descending
    events.sort(key=lambda x: x.get("exact_date", ""), reverse=True)
    return events
