import re
from datetime import datetime

# Common lab tests catalog with flexible matching patterns
LAB_TEST_PATTERNS = [
    ("Hemoglobin", [r"\bH(?:em|am)oglobin\b", r"\bHGB\b"]),
    ("Hematocrit", [r"\bH(?:em|am)atocrit\b", r"\bHCT\b"]),
    ("White Blood Cells", [r"\bWh?ite\s*Bl[o0x]+d\s*Cells?\b", r"\bWBC\b"]),
    ("Red Blood Cells", [r"\bRed\s*Bl[o0x]+d\s*Cells?\b", r"\bF[e|o]d\s*Bl[o0x]+d\b", r"\bRBC\b"]),
    ("Platelets", [r"\bPlatelets?\b", r"\bPLT\b"]),
    ("MCV", [r"\bMCV\b", r"\bMean\s*Corpuscular\s*Volume\b"]),
    ("MCH", [r"\bMCH\b"]),
    ("MCHC", [r"\bMCHC\b"]),
    ("Glucose", [r"\bGluc[o0e]se\b", r"\bFasting\s*Glucose\b"]),
    ("Blood Urea Nitrogen", [r"\bBl[o0e]+d\s*Urea\s*Nitrogen\b", r"\bBUN\b"]),
    ("Creatinine", [r"\bCreatinine\b", r"\bCREA\b"]),
    ("Sodium", [r"\bSodium\b", r"\bNA\b"]),
    ("Potassium", [r"\bPotassium\b", r"\bK\b"]),
    ("Chloride", [r"\bChloride\b", r"\bCL\b"]),
    ("Calcium", [r"\bCalcium\b", r"\bCA\b"]),
    ("Carbon Dioxide", [r"\bCarbon\s*Dioxide\b", r"\bCO2\b"]),
    ("Total Protein", [r"\bTotal\s*Protein\b"]),
    ("Albumin", [r"\bAlbumin\b", r"\bALB\b"]),
    ("Total Bilirubin", [r"\b(?:Total\s*)?Bilirubin\b"]),
    ("Alkaline Phosphatase", [r"\bAlkaline\s*Phosphatase\b", r"\bALP\b"]),
    ("AST", [r"\bAST\b", r"\bSGOT\b"]),
    ("ALT", [r"\bALT\b", r"\bSGPT\b"]),
    ("Total Cholesterol", [r"\bTotal\s*Cholesterol\b", r"\bCHOL\b"]),
    ("HDL Cholesterol", [r"\bHDL\b", r"\bHDL\s*Cholesterol\b"]),
    ("LDL Cholesterol", [r"\bLDL\b", r"\bLDL\s*Cholesterol\b"]),
    ("Triglycerides", [r"\bTriglycerides?\b", r"\bTRIG\b"]),
    ("TSH", [r"\bTSH\b", r"\bThyroid\s*Stimulating\s*Hormone\b"]),
    ("HbA1c", [r"\bHbA1c\b", r"\bGlycated\s*Hemoglobin\b"])
]

def extract_structured_data(raw_text):
    """
    Parses unstructured OCR text into standardized structured JSON.
    Preserves raw strings, decimals, and reference ranges.
    """
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    patient_info = _extract_patient_info(lines, raw_text)
    report_date = _extract_report_date(lines, raw_text)
    lab_results = _extract_lab_results(lines)
    history_items = _extract_history_items(lines, raw_text)

    return {
        "patient_information": patient_info,
        "report_date": report_date,
        "laboratory_results": lab_results,
        "medications": history_items.get("medications", []),
        "conditions": history_items.get("conditions", []),
        "allergies": history_items.get("allergies", []),
        "symptoms": history_items.get("symptoms", []),
        "observations": history_items.get("observations", []),
    }

def _extract_patient_info(lines, raw_text):
    info = {"name": None, "patient_id": None, "age": None, "sex": None}

    for line in lines:
        if not info["name"]:
            name_match = re.search(r"(?:Patient\s*(?:Name)?|Name)\s*[:\-]\s*([A-Za-z\s\.\,\'-]+?)(?=\s*(?:DOB|Age|Sex|ID|Date|Patient\s*ID|$))", line, re.IGNORECASE)
            if name_match:
                candidate = name_match.group(1).strip(" ,.-")
                candidate = re.sub(r"\s+Patient$", "", candidate, flags=re.IGNORECASE).strip()
                if len(candidate) >= 2 and not re.search(r"(Laboratory|Report|Hospital|Clinic|Doctor)", candidate, re.IGNORECASE):
                    info["name"] = candidate

        if not info["patient_id"]:
            id_match = re.search(r"(?:Patient\s*ID|MRN|Record\s*#?|PID|ID)\s*[:\-#]?\s*([A-Za-z0-9\-_]+)", line, re.IGNORECASE)
            if id_match:
                candidate_id = id_match.group(1).strip()
                if not re.search(r"^(Date|Age|Sex|Name)$", candidate_id, re.IGNORECASE):
                    info["patient_id"] = candidate_id

        if info["age"] is None:
            age_match = re.search(r"\bAge\s*[:\-]?\s*(\d{1,3})\b", line, re.IGNORECASE)
            if age_match:
                try:
                    info["age"] = int(age_match.group(1))
                except ValueError:
                    pass

        if not info["sex"]:
            sex_match = re.search(r"\b(?:Sex|Gender)\s*[:\-]?\s*(Male|Female|M|F|Other)\b", line, re.IGNORECASE)
            if sex_match:
                g = sex_match.group(1).upper()
                info["sex"] = "Male" if g in ("M", "MALE") else ("Female" if g in ("F", "FEMALE") else g)

    return info

def _extract_report_date(lines, raw_text):
    date_patterns = [
        r"(?:Report\s*Date|Date\s*of\s*Report|Collection\s*Date|Date)\s*[:\-]?\s*(\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4})",
        r"\b(\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2})\b",
        r"\b(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})\b",
        r"\b([A-Za-z]{3,9}\s+\d{1,2},\s+\d{4})\b"
    ]
    for pat in date_patterns:
        m = re.search(pat, raw_text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return datetime.now().strftime("%Y-%m-%d")

def _extract_lab_results(lines):
    results = []

    # Regex components
    val_regex = r"(?:[<>≤≥]=?\s*)?-?\d+(?:\.\d+)?"
    unit_regex = r"(?:g/dL|mg/dL|mmol/L|mEq/L|10\^3/uL|10\^6/uL|x10\^3/uL|x10\^6/uL|K/uL|M/uL|fL|pg|%|U/L|IU/L|ng/mL|pg/mL|uIU/mL|mL/min(?:/1\.73m2)?|ug/dL|mg/L|mou|ola|rosgiuL|r0s6/uL)"
    range_regex = r"(?:(?:[<>≤≥]=?\s*-?\d+(?:\.\d+)?)|(?:-?\d+(?:\.\d+)?\s*(?:-|–|—|to)\s*-?\d+(?:\.\d+)?))"

    for line in lines:
        for canonical_name, patterns in LAB_TEST_PATTERNS:
            matched_pat = None
            for p in patterns:
                if re.search(p, line, re.IGNORECASE):
                    matched_pat = p
                    break
            
            if matched_pat:
                # Extract value after test name
                subline = re.sub(matched_pat, "", line, count=1, flags=re.IGNORECASE).strip()
                
                # Search for value in subline
                val_m = re.search(rf"\b({val_regex})\b", subline)
                if val_m:
                    raw_val = val_m.group(1).strip()
                    after_val = subline[val_m.end():].strip()

                    # Extract unit
                    unit_m = re.search(rf"\b({unit_regex})\b", after_val, re.IGNORECASE)
                    unit = unit_m.group(1).strip() if unit_m else ""

                    # Clean OCR noise in unit
                    if unit in ("ola", "mgidl", "mgidl."):
                        unit = "g/dL" if "Hemoglobin" in canonical_name else "mg/dL"
                    elif unit in ("mou", "mou,"):
                        unit = "mmol/L"
                    elif "rosg" in unit or "r0s6" in unit:
                        unit = "10^3/uL" if "White" in canonical_name or "Platelet" in canonical_name else "10^6/uL"

                    # Extract reference range
                    range_m = re.search(rf"({range_regex})", after_val)
                    ref_range = range_m.group(1).strip() if range_m else "Not provided"

                    parsed_float = None
                    try:
                        clean_num = re.sub(r"[^\d\.\-]", "", raw_val)
                        if clean_num and clean_num != "-":
                            parsed_float = float(clean_num)
                    except ValueError:
                        parsed_float = None

                    if not any(r["test_name"] == canonical_name for r in results):
                        results.append({
                            "test_name": canonical_name,
                            "value": parsed_float,
                            "raw_value_str": raw_val,
                            "unit": unit,
                            "reference_range": ref_range,
                            "observation": "",
                            "source": "EXTRACTED_FROM_REPORT"
                        })
                break

    return results

def _extract_history_items(lines, raw_text):
    categories = {
        "medications": [],
        "conditions": [],
        "allergies": [],
        "symptoms": [],
        "observations": []
    }
    for line in lines:
        m_med = re.search(r"(?:Medications?|Rx|Prescription)\s*[:\-]\s*(.+)", line, re.IGNORECASE)
        if m_med:
            categories["medications"].extend([x.strip() for x in m_med.group(1).split(",") if x.strip()])
        m_all = re.search(r"(?:Allergies|Allergy)\s*[:\-]\s*(.+)", line, re.IGNORECASE)
        if m_all:
            categories["allergies"].extend([x.strip() for x in m_all.group(1).split(",") if x.strip()])
        m_cond = re.search(r"(?:Conditions?|Diagnosis|History|Past\s*Medical\s*History)\s*[:\-]\s*(.+)", line, re.IGNORECASE)
        if m_cond:
            categories["conditions"].extend([x.strip() for x in m_cond.group(1).split(",") if x.strip()])
        m_sym = re.search(r"(?:Symptoms?|Chief\s*Complaint)\s*[:\-]\s*(.+)", line, re.IGNORECASE)
        if m_sym:
            categories["symptoms"].extend([x.strip() for x in m_sym.group(1).split(",") if x.strip()])

    return categories
