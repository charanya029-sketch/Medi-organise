# AI-Powered Patient Medical Record Organization and Summarization System

A full-stack, clinically safe, and reference-range-aware web application designed to collect scattered patient medical records, process document scans (JPG, PNG, PDF) using an advanced OpenCV image preprocessing pipeline and Tesseract OCR, structure findings into a centralized database, validate numerical values **strictly against reference ranges supplied in original source reports**, and generate concise, patient-friendly AI summaries.

---

## 1. Problem Statement

Medical information is frequently fragmented across handwritten or printed prescriptions, laboratory result sheets, clinical progress notes, and diagnostic scans. When reviewing a patient's historical care trajectory:
- Healthcare providers spend valuable time piecing together disparate documents.
- Critical trends (e.g., changes in creatinine or hemoglobin across multiple visits) are obscured.
- Automated tools that attempt medical diagnosis or utilize external reference ranges risk hallucination and severe clinical errors.

## 2. Objectives & Core Principles

1. **Centralized Patient Intake & History**: Unify demographic data, clinical symptoms, pre-existing conditions, allergies, and current medications.
2. **Advanced Image Preprocessing**: Improve readability of poor-quality or wrinkled document scans before OCR.
3. **Multi-Pass OCR & Provenance Tracking**: Extract text while preserving exact decimal values and tagging every data point with its origin (`USER_PROVIDED`, `EXTRACTED_FROM_REPORT`, `AI_GENERATED`, `USER_VERIFIED`, `USER_CORRECTED`).
4. **Strict Reference-Range Awareness**: Classify laboratory results (`LOW`, `NORMAL`, `HIGH`) **solely** based on ranges printed on the original report. If a reference range is missing, status is strictly marked as `Not determined` and range as `Not provided`.
5. **No Diagnosis or Prescription**: The system is an administrative organization and summarization system. It does NOT diagnose diseases, predict conditions, or suggest medical treatments.
6. **Side-by-Side Verification Interface**: Allow users to inspect extracted values directly alongside the original scan with zoom controls, correct any errors, and confirm before final persistence.

---

## 3. System Architecture & Data Flow

```
[Medical Report Scan (JPG, PNG, PDF)]
                 │
                 ▼
┌────────────────────────────────────────┐
│ 1. Secure Ingestion & Original Archive │
│    - Retains original file untouched   │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│ 2. OpenCV Image Preprocessing Pipeline │
│    - Upscale / Bicubic Interpolation   │
│    - Grayscale Conversion              │
│    - Bilateral Denoising               │
│    - CLAHE Contrast Enhancement        │
│    - Unsharp Mask Sharpening           │
│    - Adaptive & Otsu Thresholding      │
│    - Automated Deskewing               │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│ 3. Multi-Pass OCR (pytesseract)        │
│    - Layout-aware PSM parsing          │
│    - Word-level confidence tracking    │
│    - Raw OCR text preserved for audit  │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│ 4. AI & Pattern Data Structuring       │
│    - Predefined standard JSON format   │
│    - Safe LLM API (OpenRouter/Gemini)  │
│    - Deterministic fallback engine     │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│ 5. Validation & Reference Range Engine │
│    - Rule: value < lower -> LOW        │
│    - Rule: lower <= value <= high      │
│            -> NORMAL                   │
│    - Rule: value > high -> HIGH        │
│    - Missing range -> Not determined   │
│    - Suspicious decimal/outlier        │
│      -> "Needs verification"           │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│ 6. Interactive Verification Interface  │
│    - Side-by-side original image view  │
│    - Editable values and units         │
│    - Human audit & confirmation        │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│ 7. Relational SQLite/SQLAlchemy DB     │
│    - Patients, Reports, Labs, History  │
└────────┬───────────────────────┬───────┘
         │                       │
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│ History Engine   │    │ Patient Summary  │
│ - Timeline view  │    │ - Patient-ready  │
│ - Test filtering │    │ - Factual & safe │
└──────────────────┘    └──────────────────┘
```

---

## 4. Technology Stack

- **Backend**: Python 3.12, Flask, Flask-SQLAlchemy, Werkzeug
- **Database**: SQLite (default), SQLAlchemy ORM (PostgreSQL ready)
- **Computer Vision & OCR**: OpenCV (`opencv-python-headless`), Pillow, `pytesseract`, Tesseract OCR Engine
- **AI Integration**: OpenRouter API (`google/gemini-2.0-flash-001` or OpenAI-compatible models) + Offline Deterministic Medical Structuring Fallback
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5, Bootstrap Icons, responsive mobile/tablet layout
- **Testing**: `pytest`

---

## 5. Installation & Setup Instructions

### Prerequisites
- Python 3.10+ installed
- Tesseract OCR engine installed on system

### A. Windows Installation

1. **Clone or Navigate to the Project**:
   ```powershell
   cd C:\Users\chara\.gemini\antigravity\scratch\medical-record-ai
   ```

2. **Install Python Dependencies**:
   ```powershell
   python -m pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
   Edit `.env` if you wish to configure your OpenRouter API key or specify a custom Tesseract path:
   ```env
   OPENROUTER_API_KEY=your_key_here
   OPENROUTER_MODEL=google/gemini-2.0-flash-001
   TESSERACT_PATH=C:\Users\chara\AppData\Local\Programs\Tesseract-OCR\tesseract.exe
   ```
   *(Note: If `OPENROUTER_API_KEY` is not provided, the application runs automatically using the built-in deterministic factual summarizer and regex structuring engine without external API calls.)*

4. **Seed Database with Sample Patients & Reports**:
   ```powershell
   python seed_data.py
   ```

5. **Run Automated Tests**:
   ```powershell
   python -m pytest -v
   ```

6. **Start the Application**:
   ```powershell
   python app.py
   ```
   Open your browser at `http://127.0.0.1:5000`.

---

### B. Linux / macOS Installation

1. **Install Tesseract OCR**:
   - Ubuntu/Debian: `sudo apt update && sudo apt install tesseract-ocr libtesseract-dev`
   - macOS: `brew install tesseract`

2. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   ```bash
   cp .env.example .env
   ```

4. **Seed & Run**:
   ```bash
   python seed_data.py
   python app.py
   ```

---

## 6. Website Pages & Workflow

### 1. Landing Page (`/`)
- Professional healthcare theme highlighting data safety, document preprocessing workflow, and clear non-diagnostic disclaimers.
- Quick action buttons to launch the dashboard or upload a medical document.

### 2. Dashboard (`/dashboard`)
- Real-time clinical statistics: Total Patients, Total Uploaded Reports, Extracted Lab Results.
- Global patient search by Patient ID or Name.
- Quick navigation tables showing recent patients and uploaded reports.

### 3. Patient Intake & Directory (`/patients`)
- Modal form for structured patient registration: Patient ID (unique), Full Name, Age, Sex, Symptoms, Pre-existing Conditions, Allergies, Current Medications, and Clinical Notes.
- Intake records are tagged with **Source: User Provided**.

### 4. Patient Profile (`/patients/<patient_id>`)
- **Patient Overview**: Demographics, symptoms, pre-existing conditions, allergies, and medications with source badges.
- **Laboratory Results**: Interactive table displaying Test Name, Value, Unit, Report Reference Range, Status Badge (`LOW`, `NORMAL`, `HIGH`, `Needs verification`), and Provenance.
- **Medical Reports**: Chronological archive of uploaded documents with links to raw files and verification audits.
- **Medical Timeline**: Visual chronological history of visits, report uploads, and clinical entries.
- **AI Summary**: Concise, patient-friendly summary strictly summarizing available records.

### 5. Report Upload (`/upload`)
- Accepts JPG, PNG, and PDF files up to 16MB.
- Retains original document untouched, applies OpenCV preprocessing (CLAHE, Denoise, Sharpen, Deskew), runs multi-pass OCR, and redirects to the verification interface.

### 6. Report Verification Interface (`/reports/verify/<report_id>`)
- **Side-by-Side Split View**:
  - Left: Interactive source document viewer with zoom controls (Zoom In, Zoom Out, Reset).
  - Right: Editable table of extracted lab results with word confidence badges (`High`, `Medium`, `Low`).
- Allows doctors or patients to correct OCR misreadings (e.g. missing decimal point) before committing to the database.
- Marks confirmed entries as `USER_VERIFIED` or `USER_CORRECTED`.

### 7. Patient History Retrieval (`/patients/<patient_id>/history`)
- Chronological archive of all historical laboratory tests and clinical history entries.
- Filter by test name (e.g., "Show previous glucose tests" or "Hemoglobin") to evaluate test results over time.

---

## 7. REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/patients` | Retrieve all patients (supports `?q=` search query) |
| `POST` | `/api/patients` | Register a new patient profile |
| `GET` | `/api/patients/<patient_id>` | Get specific patient details |
| `PUT` | `/api/patients/<patient_id>` | Update patient intake information |
| `GET` | `/api/patients/<patient_id>/reports` | List all reports associated with a patient |
| `GET` | `/api/patients/<patient_id>/lab-results` | List all laboratory results (supports `?test_name=`) |
| `GET` | `/api/patients/<patient_id>/history` | List clinical history items (supports `?category=`) |
| `POST` | `/api/patients/<patient_id>/summarize` | Trigger on-demand AI summary generation |

---

## 8. Clinical Safety & Legal Disclaimers

> [!IMPORTANT]
> **Administrative Tool Only**: This web application is an administrative data organization and summarization tool. It is **NOT** a medical diagnostic device, does **NOT** predict illnesses, does **NOT** suggest therapeutic courses or treatment plans, and does **NOT** issue medical prescriptions.

> [!NOTE]
> **Source-Report Exclusivity**: Laboratory values are compared **only** against the reference ranges explicitly printed in the original medical report. The system never applies external population averages or AI assumptions to judge medical normalcy.

---

## 9. Testing & Verification

The application includes a comprehensive test suite in `tests/`:
- `test_patient_intake.py`: Valid registration, missing field enforcement, duplicate ID rejection, invalid age handling.
- `test_preprocessing.py`: Verifies OpenCV resizing, grayscale, denoising, CLAHE, and deskewing outputs.
- `test_extraction.py`: Verifies decimal precision (`10.2`, `1.3`), unit extraction, dates, and reference ranges.
- `test_validation.py`: Tests `LOW`, `NORMAL`, `HIGH`, missing range (`Not determined`), and outlier/low-confidence flagging (`Needs verification`).
- `test_history.py`: Verifies patient-specific test queries and chronological sorting.
- `test_ai_safety.py`: Enforces system prompt safety constraints, disclaimer generation, and provenance tracking.
- `test_e2e_flow.py`: Full end-to-end simulation from patient intake to report upload, verification, and AI summary.

Run all tests:
```powershell
pytest -v
```
