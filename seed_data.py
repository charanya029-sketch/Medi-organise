import os
from datetime import datetime, timezone, timedelta
from app import create_app
from config import Config
from models import db, Patient, MedicalReport, LaboratoryResult, MedicalHistory, Summary
from services.ai_service import generate_patient_summary

app = create_app(Config)
with app.app_context():
    # Clear existing tables for fresh seed
    db.drop_all()
    db.create_all()
    print("Initialized database schema.")

    # 1. Patient 1: Jane Doe
    p1 = Patient(
        patient_id="PT-2026-001",
        name="Jane Doe",
        age=42,
        sex="Female",
        symptoms="Mild fatigue, intermittent cold intolerance",
        conditions="Pre-existing Iron Deficiency Anemia (resolved 2024)",
        allergies="Penicillin, Sulfa drugs",
        medications="Ferrous sulfate 325mg daily, Multivitamin",
        additional_notes="Routine annual diagnostic hematology checkup.",
        created_at=datetime.now(timezone.utc) - timedelta(days=90)
    )
    db.session.add(p1)

    # Patient 1 History items
    db.session.add(MedicalHistory(patient_id="PT-2026-001", category="Allergy", information="Penicillin (Hives / Rash)", source="USER_PROVIDED", date="2020-03-15"))
    db.session.add(MedicalHistory(patient_id="PT-2026-001", category="Allergy", information="Sulfa drugs (Nausea)", source="USER_PROVIDED", date="2021-08-10"))
    db.session.add(MedicalHistory(patient_id="PT-2026-001", category="Condition", information="Iron Deficiency Anemia", source="USER_PROVIDED", date="2023-01-10"))
    db.session.add(MedicalHistory(patient_id="PT-2026-001", category="Medication", information="Ferrous sulfate 325mg daily", source="USER_PROVIDED", date="2026-01-05"))

    # Patient 1 Report: CBC
    r1 = MedicalReport(
        patient_id="PT-2026-001",
        report_type="Laboratory Report",
        file_name="sample_cbc_report.png",
        file_path="uploads/sample_cbc_report.png",
        preprocessed_path="uploads/preprocessed/sample_cbc_report_preprocessed.png",
        report_date="2026-05-12",
        raw_ocr_text="DIAGNOSTIC HEMATOLOGY - COMPLETE BLOOD COUNT (CBC)\nPatient Name: Jane Doe Patient ID: PT-2026-001 Age: 42 Sex: Female\nHemoglobin 10.2 g/dL (Reference: 12.0 - 16.0) LOW\nHematocrit 31.5 % (Reference: 37.0 - 48.0) LOW\nPlatelets 245 10^3/uL (Reference: 150 - 450) NORMAL\nWhite Blood Cells 6.8 10^3/uL (Reference: 4.5 - 11.0) NORMAL",
        status="VERIFIED",
        created_at=datetime.now(timezone.utc) - timedelta(days=60)
    )
    db.session.add(r1)
    db.session.flush()

    # Patient 1 Labs
    labs_p1 = [
        LaboratoryResult(report_id=r1.id, patient_id="PT-2026-001", test_name="Hemoglobin", value=10.2, raw_value_str="10.2", unit="g/dL", reference_range="12.0 - 16.0", lower_limit=12.0, upper_limit=16.0, status="LOW", confidence="High", user_verified=True, source="USER_VERIFIED", created_at=datetime.now(timezone.utc) - timedelta(days=60)),
        LaboratoryResult(report_id=r1.id, patient_id="PT-2026-001", test_name="Hematocrit", value=31.5, raw_value_str="31.5", unit="%", reference_range="37.0 - 48.0", lower_limit=37.0, upper_limit=48.0, status="LOW", confidence="High", user_verified=True, source="USER_VERIFIED", created_at=datetime.now(timezone.utc) - timedelta(days=60)),
        LaboratoryResult(report_id=r1.id, patient_id="PT-2026-001", test_name="Platelets", value=245.0, raw_value_str="245", unit="10^3/uL", reference_range="150 - 450", lower_limit=150.0, upper_limit=450.0, status="NORMAL", confidence="High", user_verified=True, source="USER_VERIFIED", created_at=datetime.now(timezone.utc) - timedelta(days=60)),
        LaboratoryResult(report_id=r1.id, patient_id="PT-2026-001", test_name="White Blood Cells", value=6.8, raw_value_str="6.8", unit="10^3/uL", reference_range="4.5 - 11.0", lower_limit=4.5, upper_limit=11.0, status="NORMAL", confidence="High", user_verified=True, source="USER_VERIFIED", created_at=datetime.now(timezone.utc) - timedelta(days=60))
    ]
    db.session.add_all(labs_p1)

    # 2. Patient 2: Robert Smith
    p2 = Patient(
        patient_id="PT-2026-002",
        name="Robert Smith",
        age=58,
        sex="Male",
        symptoms="Occasional nocturia, mild lower back stiffness",
        conditions="Essential Hypertension, Type 2 Diabetes Mellitus",
        allergies="None known",
        medications="Metformin 500mg BID, Lisinopril 20mg daily",
        additional_notes="Routine metabolic and kidney function surveillance.",
        created_at=datetime.now(timezone.utc) - timedelta(days=45)
    )
    db.session.add(p2)

    db.session.add(MedicalHistory(patient_id="PT-2026-002", category="Condition", information="Essential Hypertension", source="USER_PROVIDED", date="2018-05-20"))
    db.session.add(MedicalHistory(patient_id="PT-2026-002", category="Condition", information="Type 2 Diabetes Mellitus", source="USER_PROVIDED", date="2020-11-12"))
    db.session.add(MedicalHistory(patient_id="PT-2026-002", category="Medication", information="Metformin 500mg BID", source="USER_PROVIDED", date="2020-11-15"))
    db.session.add(MedicalHistory(patient_id="PT-2026-002", category="Medication", information="Lisinopril 20mg daily", source="USER_PROVIDED", date="2018-06-01"))

    # Patient 2 Report: CMP
    r2 = MedicalReport(
        patient_id="PT-2026-002",
        report_type="Laboratory Report",
        file_name="sample_metabolic_panel.png",
        file_path="uploads/sample_metabolic_panel.png",
        preprocessed_path="uploads/preprocessed/sample_metabolic_panel_preprocessed.png",
        report_date="2026-06-18",
        raw_ocr_text="CLINICAL CHEMISTRY - COMPREHENSIVE METABOLIC PANEL\nPatient Name: Robert Smith Patient ID: PT-2026-002 Age: 58 Sex: Male\nGlucose 95 mg/dL (Reference: 70 - 99) NORMAL\nBlood Urea Nitrogen 18 mg/dL (Reference: 7 - 20) NORMAL\nCreatinine 1.3 mg/dL (Reference: 0.6 - 1.2) HIGH\nSodium 140 mmol/L (Reference: 136 - 145) NORMAL\nPotassium 4.2 mmol/L (Reference: 3.5 - 5.1) NORMAL",
        status="VERIFIED",
        created_at=datetime.now(timezone.utc) - timedelta(days=20)
    )
    db.session.add(r2)
    db.session.flush()

    # Patient 2 Labs
    labs_p2 = [
        LaboratoryResult(report_id=r2.id, patient_id="PT-2026-002", test_name="Glucose", value=95.0, raw_value_str="95", unit="mg/dL", reference_range="70 - 99", lower_limit=70.0, upper_limit=99.0, status="NORMAL", confidence="High", user_verified=True, source="USER_VERIFIED", created_at=datetime.now(timezone.utc) - timedelta(days=20)),
        LaboratoryResult(report_id=r2.id, patient_id="PT-2026-002", test_name="Blood Urea Nitrogen", value=18.0, raw_value_str="18", unit="mg/dL", reference_range="7 - 20", lower_limit=7.0, upper_limit=20.0, status="NORMAL", confidence="High", user_verified=True, source="USER_VERIFIED", created_at=datetime.now(timezone.utc) - timedelta(days=20)),
        LaboratoryResult(report_id=r2.id, patient_id="PT-2026-002", test_name="Creatinine", value=1.3, raw_value_str="1.3", unit="mg/dL", reference_range="0.6 - 1.2", lower_limit=0.6, upper_limit=1.2, status="HIGH", confidence="High", user_verified=True, source="USER_VERIFIED", created_at=datetime.now(timezone.utc) - timedelta(days=20)),
        LaboratoryResult(report_id=r2.id, patient_id="PT-2026-002", test_name="Sodium", value=140.0, raw_value_str="140", unit="mmol/L", reference_range="136 - 145", lower_limit=136.0, upper_limit=145.0, status="NORMAL", confidence="High", user_verified=True, source="USER_VERIFIED", created_at=datetime.now(timezone.utc) - timedelta(days=20)),
        LaboratoryResult(report_id=r2.id, patient_id="PT-2026-002", test_name="Potassium", value=4.2, raw_value_str="4.2", unit="mmol/L", reference_range="3.5 - 5.1", lower_limit=3.5, upper_limit=5.1, status="NORMAL", confidence="High", user_verified=True, source="USER_VERIFIED", created_at=datetime.now(timezone.utc) - timedelta(days=20)),
    ]
    db.session.add_all(labs_p2)

    db.session.commit()

    # Generate initial AI summaries for both seeded patients
    for pt in [p1, p2]:
        labs = LaboratoryResult.query.filter_by(patient_id=pt.patient_id).all()
        hist = MedicalHistory.query.filter_by(patient_id=pt.patient_id).all()
        s_res = generate_patient_summary(pt.to_dict(), [l.to_dict() for l in labs], [h.to_dict() for h in hist])
        db.session.add(Summary(patient_id=pt.patient_id, summary_text=s_res["summary_text"], source=s_res["source"]))
    db.session.commit()

    print("Seed data loaded successfully! 2 patients, 2 reports, 9 lab results, and AI summaries created.")
