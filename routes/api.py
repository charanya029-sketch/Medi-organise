from flask import Blueprint, request, jsonify, current_app
from models import db, Patient, MedicalReport, LaboratoryResult, MedicalHistory, Summary
from services.ai_service import generate_patient_summary, structure_report_with_ai
from services.ocr_service import run_ocr
from services.image_preprocessing import preprocess_medical_image
from services.validation_service import validate_structured_report
from werkzeug.utils import secure_filename
from pathlib import Path
import uuid

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/patients", methods=["GET"])
def get_patients():
    q = request.args.get("q", "").strip()
    if q:
        patients = Patient.query.filter(
            (Patient.patient_id.ilike(f"%{q}%")) | (Patient.name.ilike(f"%{q}%"))
        ).all()
    else:
        patients = Patient.query.all()
    return jsonify({"status": "success", "count": len(patients), "data": [p.to_dict() for p in patients]})

@api_bp.route("/patients", methods=["POST"])
def create_patient():
    data = request.get_json() or {}
    patient_id = data.get("patient_id", "").strip()
    name = data.get("name", "").strip()

    if not patient_id or not name:
        return jsonify({"status": "error", "message": "patient_id and name are required."}), 400

    if Patient.query.filter_by(patient_id=patient_id).first():
        return jsonify({"status": "error", "message": f"Patient '{patient_id}' already exists."}), 409

    patient = Patient(
        patient_id=patient_id,
        name=name,
        age=data.get("age"),
        sex=data.get("sex"),
        symptoms=data.get("symptoms"),
        conditions=data.get("conditions"),
        allergies=data.get("allergies"),
        medications=data.get("medications"),
        additional_notes=data.get("additional_notes")
    )
    db.session.add(patient)

    if data.get("symptoms"):
        db.session.add(MedicalHistory(patient_id=patient_id, category="Symptom", information=data["symptoms"], source="USER_PROVIDED"))
    if data.get("conditions"):
        db.session.add(MedicalHistory(patient_id=patient_id, category="Condition", information=data["conditions"], source="USER_PROVIDED"))
    if data.get("allergies"):
        db.session.add(MedicalHistory(patient_id=patient_id, category="Allergy", information=data["allergies"], source="USER_PROVIDED"))
    if data.get("medications"):
        db.session.add(MedicalHistory(patient_id=patient_id, category="Medication", information=data["medications"], source="USER_PROVIDED"))

    db.session.commit()
    return jsonify({"status": "success", "data": patient.to_dict()}), 201

@api_bp.route("/patients/<patient_id>", methods=["GET"])
def get_patient(patient_id):
    patient = Patient.query.filter_by(patient_id=patient_id).first()
    if not patient:
        return jsonify({"status": "error", "message": "Patient not found."}), 404
    return jsonify({"status": "success", "data": patient.to_dict()})

@api_bp.route("/patients/<patient_id>", methods=["PUT"])
def update_patient(patient_id):
    patient = Patient.query.filter_by(patient_id=patient_id).first()
    if not patient:
        return jsonify({"status": "error", "message": "Patient not found."}), 404

    data = request.get_json() or {}
    if "name" in data:
        patient.name = data["name"]
    if "age" in data:
        patient.age = data["age"]
    if "sex" in data:
        patient.sex = data["sex"]
    if "symptoms" in data:
        patient.symptoms = data["symptoms"]
    if "conditions" in data:
        patient.conditions = data["conditions"]
    if "allergies" in data:
        patient.allergies = data["allergies"]
    if "medications" in data:
        patient.medications = data["medications"]
    if "additional_notes" in data:
        patient.additional_notes = data["additional_notes"]

    db.session.commit()
    return jsonify({"status": "success", "data": patient.to_dict()})

@api_bp.route("/patients/<patient_id>/reports", methods=["GET"])
def get_patient_reports(patient_id):
    reports = MedicalReport.query.filter_by(patient_id=patient_id).order_by(MedicalReport.created_at.desc()).all()
    return jsonify({"status": "success", "count": len(reports), "data": [r.to_dict() for r in reports]})

@api_bp.route("/patients/<patient_id>/lab-results", methods=["GET"])
def get_patient_lab_results(patient_id):
    test_name = request.args.get("test_name")
    q = LaboratoryResult.query.filter_by(patient_id=patient_id)
    if test_name:
        q = q.filter(LaboratoryResult.test_name.ilike(f"%{test_name}%"))
    results = q.order_by(LaboratoryResult.created_at.desc()).all()
    return jsonify({"status": "success", "count": len(results), "data": [r.to_dict() for r in results]})

@api_bp.route("/patients/<patient_id>/history", methods=["GET"])
def get_patient_history(patient_id):
    category = request.args.get("category")
    q = MedicalHistory.query.filter_by(patient_id=patient_id)
    if category:
        q = q.filter(MedicalHistory.category.ilike(f"%{category}%"))
    histories = q.order_by(MedicalHistory.created_at.desc()).all()
    return jsonify({"status": "success", "count": len(histories), "data": [h.to_dict() for h in histories]})

@api_bp.route("/patients/<patient_id>/summarize", methods=["POST"])
def summarize_patient_api(patient_id):
    patient = Patient.query.filter_by(patient_id=patient_id).first()
    if not patient:
        return jsonify({"status": "error", "message": "Patient not found."}), 404

    lab_results = LaboratoryResult.query.filter_by(patient_id=patient_id).all()
    histories = MedicalHistory.query.filter_by(patient_id=patient_id).all()

    summary_res = generate_patient_summary(
        patient.to_dict(),
        [l.to_dict() for l in lab_results],
        [h.to_dict() for h in histories]
    )

    summary_record = Summary(
        patient_id=patient_id,
        summary_text=summary_res["summary_text"],
        source=summary_res["source"]
    )
    db.session.add(summary_record)
    db.session.commit()

    return jsonify({"status": "success", "data": summary_record.to_dict()})
