import os
import uuid
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
from werkzeug.utils import secure_filename
from models import db, Patient, MedicalReport, LaboratoryResult, MedicalHistory
from services.image_preprocessing import preprocess_medical_image
from services.ocr_service import run_ocr
from services.ai_service import structure_report_with_ai
from services.validation_service import validate_structured_report, evaluate_laboratory_value

reports_bp = Blueprint("reports", __name__)

def allowed_file(filename):
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "pdf"})
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed

@reports_bp.route("/upload", methods=["GET", "POST"])
def upload_report():
    patients = Patient.query.order_by(Patient.name.asc()).all()
    selected_pid = request.args.get("patient_id", "")

    if request.method == "POST":
        patient_id = request.form.get("patient_id", "").strip()
        report_type = request.form.get("report_type", "Laboratory Report").strip()
        file = request.files.get("report_file")

        if not patient_id:
            flash("Please select or specify a valid Patient ID.", "danger")
            return redirect(url_for("reports.upload_report"))

        patient = Patient.query.filter_by(patient_id=patient_id).first()
        if not patient:
            # If patient does not exist, create a basic record from upload form
            patient_name = request.form.get("new_patient_name", f"Patient {patient_id}").strip()
            patient = Patient(patient_id=patient_id, name=patient_name)
            db.session.add(patient)
            db.session.commit()

        if not file or file.filename == "":
            flash("No file was selected for upload.", "danger")
            return redirect(url_for("reports.upload_report", patient_id=patient_id))

        if not allowed_file(file.filename):
            flash("Unsupported file format. Please upload JPG, PNG, or PDF files.", "danger")
            return redirect(url_for("reports.upload_report", patient_id=patient_id))

        # 1. Securely save original file
        upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
        upload_dir.mkdir(parents=True, exist_ok=True)

        orig_filename = secure_filename(file.filename)
        unique_prefix = uuid.uuid4().hex[:8]
        saved_filename = f"{unique_prefix}_{orig_filename}"
        saved_path = upload_dir / saved_filename
        file.save(str(saved_path))

        try:
            # 2. Image Preprocessing Pipeline
            prep_dir = upload_dir / "preprocessed"
            prep_result = preprocess_medical_image(saved_path, output_dir=prep_dir)

            # 3. Multi-pass OCR Processing
            ocr_result = run_ocr(prep_result)

            # 4. AI / Pattern-guided Structuring
            structured = structure_report_with_ai(ocr_result["raw_text"])

            # 5. Validation against Report-provided Reference Ranges
            validated = validate_structured_report(structured, ocr_confidence=ocr_result["confidence"])

            # 6. Create MedicalReport record in DB (PENDING_VERIFICATION)
            rep_date = validated.get("report_date") or None
            report = MedicalReport(
                patient_id=patient_id,
                report_type=report_type,
                file_name=orig_filename,
                file_path=str(saved_path.relative_to(upload_dir.parent)),
                preprocessed_path=str(Path(prep_result["primary_processed_path"]).relative_to(upload_dir.parent)),
                report_date=rep_date,
                raw_ocr_text=ocr_result["raw_text"],
                status="PENDING_VERIFICATION"
            )
            db.session.add(report)
            db.session.flush()  # to obtain report.id

            # 7. Insert extracted lab results linked to this report
            for lab in validated.get("laboratory_results", []):
                val_float = lab.get("value")
                raw_str = lab.get("raw_value_str") or (str(val_float) if val_float is not None else "")
                lab_obj = LaboratoryResult(
                    report_id=report.id,
                    patient_id=patient_id,
                    test_name=lab.get("test_name", "Unknown Test"),
                    value=val_float,
                    raw_value_str=raw_str,
                    unit=lab.get("unit", ""),
                    reference_range=lab.get("reference_range", "Not provided"),
                    lower_limit=lab.get("lower_limit"),
                    upper_limit=lab.get("upper_limit"),
                    status=lab.get("status", "Not determined"),
                    confidence=lab.get("confidence", "High"),
                    verification_required=lab.get("verification_required", False),
                    user_verified=False,
                    user_corrected=False,
                    source="EXTRACTED_FROM_REPORT"
                )
                db.session.add(lab_obj)

            # Also check if any clinical history entries were extracted
            for cond in validated.get("conditions", []):
                db.session.add(MedicalHistory(patient_id=patient_id, category="Condition", information=cond, source="EXTRACTED_FROM_REPORT", date=rep_date))
            for med in validated.get("medications", []):
                db.session.add(MedicalHistory(patient_id=patient_id, category="Medication", information=med, source="EXTRACTED_FROM_REPORT", date=rep_date))
            for allg in validated.get("allergies", []):
                db.session.add(MedicalHistory(patient_id=patient_id, category="Allergy", information=allg, source="EXTRACTED_FROM_REPORT", date=rep_date))

            db.session.commit()

            flash(f"Report uploaded successfully! OCR extracted {len(validated.get('laboratory_results', []))} tests with {ocr_result['confidence']}% average confidence. Please verify the findings below.", "info")
            return redirect(url_for("reports.verify_report", report_id=report.id))

        except Exception as e:
            current_app.logger.error(f"Error processing report upload: {e}", exc_info=True)
            flash(f"An error occurred while processing the report: {str(e)}", "danger")
            return redirect(url_for("reports.upload_report", patient_id=patient_id))

    return render_template("upload.html", patients=patients, selected_pid=selected_pid)

@reports_bp.route("/reports/verify/<int:report_id>")
def verify_report(report_id):
    report = db.session.get(MedicalReport, report_id)
    if not report:
        from flask import abort
        abort(404)
    patient = Patient.query.filter_by(patient_id=report.patient_id).first_or_404()
    lab_results = LaboratoryResult.query.filter_by(report_id=report.id).all()

    return render_template(
        "verify_report.html",
        report=report,
        patient=patient,
        lab_results=lab_results
    )

@reports_bp.route("/reports/confirm/<int:report_id>", methods=["POST"])
def confirm_report(report_id):
    report = db.session.get(MedicalReport, report_id)
    if not report:
        from flask import abort
        abort(404)
    lab_results = LaboratoryResult.query.filter_by(report_id=report.id).all()

    # Process user edits/confirmations for each row
    for lab in lab_results:
        prefix = f"lab_{lab.id}_"
        form_name = request.form.get(f"{prefix}test_name", lab.test_name).strip()
        form_val_str = request.form.get(f"{prefix}value", lab.raw_value_str).strip()
        form_unit = request.form.get(f"{prefix}unit", lab.unit).strip()
        form_range = request.form.get(f"{prefix}reference_range", lab.reference_range).strip()

        # Check if user made corrections
        is_corrected = (
            form_name != lab.test_name or
            form_val_str != lab.raw_value_str or
            form_unit != (lab.unit or "") or
            form_range != (lab.reference_range or "")
        )

        parsed_float = None
        try:
            parsed_float = float(form_val_str)
        except ValueError:
            parsed_float = lab.value

        # Re-evaluate against report reference range
        evaluation = evaluate_laboratory_value(parsed_float, form_range, ocr_confidence=100.0)

        lab.test_name = form_name
        lab.value = parsed_float
        lab.raw_value_str = form_val_str
        lab.unit = form_unit
        lab.reference_range = evaluation["reference_range"]
        lab.lower_limit = evaluation["lower_limit"]
        lab.upper_limit = evaluation["upper_limit"]
        lab.status = evaluation["status"]
        lab.verification_required = False
        lab.user_verified = True
        lab.user_corrected = is_corrected
        lab.confidence = "High"
        lab.source = "USER_CORRECTED" if is_corrected else "USER_VERIFIED"

    report.status = "VERIFIED"
    db.session.commit()

    flash("Report verification complete! All laboratory values have been confirmed and stored in the patient record.", "success")
    return redirect(url_for("patients.patient_profile", patient_id=report.patient_id))

@reports_bp.route("/uploads/<path:filename>")
def serve_upload(filename):
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(upload_dir, filename)
