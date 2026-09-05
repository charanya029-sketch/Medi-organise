import json
import requests
from flask import current_app

AI_STRUCTURING_SYSTEM_PROMPT = """You are a medical information organization assistant.
Your task is to convert OCR-extracted text from a medical report into structured JSON.

CRITICAL SAFETY AND FIDELITY RULES:
1. Extract ONLY information explicitly present in the provided text.
2. DO NOT invent, assume, or hallucinate missing information.
3. If a field is not present, set it to null or an empty list/string.
4. DO NOT change numerical values or decimals (e.g., preserve exact numbers like 10.2, 1.3).
5. DO NOT provide medical diagnosis, disease predictions, or treatment/medication recommendations.
6. Return valid JSON only, matching this structure:
{
  "patient_information": {
    "name": null,
    "patient_id": null,
    "age": null,
    "sex": null
  },
  "report_date": null,
  "laboratory_results": [
    {
      "test_name": "Test Name",
      "value": 0.0,
      "raw_value_str": "0.0",
      "unit": "unit",
      "reference_range": "e.g. 12-16 or Not provided",
      "observation": "",
      "source": "EXTRACTED_FROM_REPORT"
    }
  ],
  "medications": [],
  "conditions": [],
  "allergies": [],
  "symptoms": [],
  "observations": []
}
"""

AI_SUMMARY_SYSTEM_PROMPT = """You are a medical information summarization assistant.
Summarize ONLY the structured patient information and laboratory results provided to you.

STRICT SAFETY AND MEDICAL RULES:
1. Do NOT diagnose any disease or condition.
2. Do NOT predict diseases.
3. Do NOT recommend treatments, lifestyle changes, or procedures.
4. Do NOT recommend or prescribe medications.
5. Do NOT provide medical advice.
6. Do NOT invent missing values or reference ranges.
7. Do NOT modify laboratory values.
8. Clearly distinguish information entered by the user (User Provided) from information extracted from medical reports (Extracted from Report).
9. Mention abnormal, low, or high test results ONLY when they were already determined using the reference range supplied directly in the source report.
10. The summary must be concise, patient-friendly, easy to understand, factual, and strictly grounded in the provided data.
11. Include a clear disclaimer that this summary is for informational organization only and not medical advice.
"""

def structure_report_with_ai(raw_ocr_text, api_key=None, model=None, base_url=None):
    """
    Sends raw OCR text to LLM to produce structured JSON.
    Falls back to deterministic rule-based extractor if API is unavailable or unconfigured.
    """
    if not api_key:
        api_key = current_app.config.get("OPENROUTER_API_KEY", "") if current_app else ""
    if not model:
        model = current_app.config.get("OPENROUTER_MODEL", "google/gemini-2.0-flash-001") if current_app else "google/gemini-2.0-flash-001"
    if not base_url:
        base_url = current_app.config.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1") if current_app else "https://openrouter.ai/api/v1"

    if api_key and str(api_key).strip() and not str(api_key).startswith("your_"):
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://medical-records-system.local",
                "X-Title": "Medical Record AI",
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": AI_STRUCTURING_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Extract structured data from this medical report OCR text:\n\n{raw_ocr_text}"}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1,
                "max_tokens": 2048,
            }
            resp = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                parsed["ai_source"] = "AI_GENERATED (LLM)"
                return parsed
        except Exception as e:
            # Gracefully degrade to deterministic extraction
            if current_app:
                current_app.logger.warning(f"LLM API Structuring failed: {e}. Using deterministic fallback.")

    # Deterministic fallback using extraction_service
    from .extraction_service import extract_structured_data
    result = extract_structured_data(raw_ocr_text)
    result["ai_source"] = "DETERMINISTIC_PARSER_FALLBACK"
    return result

def generate_patient_summary(patient_data, lab_results, histories, api_key=None, model=None, base_url=None):
    """
    Generates a concise, patient-friendly, strictly factual medical summary.
    Uses structured data as primary input.
    Falls back to deterministic factual summarizer if LLM API is unavailable.
    """
    if not api_key:
        api_key = current_app.config.get("OPENROUTER_API_KEY", "") if current_app else ""
    if not model:
        model = current_app.config.get("OPENROUTER_MODEL", "google/gemini-2.0-flash-001") if current_app else "google/gemini-2.0-flash-001"
    if not base_url:
        base_url = current_app.config.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1") if current_app else "https://openrouter.ai/api/v1"

    context = {
        "patient": {
            "patient_id": patient_data.get("patient_id"),
            "name": patient_data.get("name"),
            "age": patient_data.get("age"),
            "sex": patient_data.get("sex"),
            "symptoms": patient_data.get("symptoms"),
            "conditions": patient_data.get("conditions"),
            "allergies": patient_data.get("allergies"),
            "medications": patient_data.get("medications"),
        },
        "laboratory_results": [
            {
                "test": l.get("test_name"),
                "value": l.get("value") if l.get("value") is not None else l.get("raw_value_str"),
                "unit": l.get("unit"),
                "reference_range": l.get("reference_range", "Not provided"),
                "status": l.get("status"),
                "source": l.get("source")
            }
            for l in lab_results
        ],
        "recorded_history": [
            {"category": h.get("category"), "information": h.get("information"), "source": h.get("source")}
            for h in histories
        ]
    }

    if api_key and str(api_key).strip() and not str(api_key).startswith("your_"):
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://medical-records-system.local",
                "X-Title": "Medical Record AI",
            }
            prompt_content = f"Summarize this structured patient medical record:\n\n{json.dumps(context, indent=2)}"
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": AI_SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_content}
                ],
                "temperature": 0.2,
                "max_tokens": 1024,
            }
            resp = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                summary_text = resp.json()["choices"][0]["message"]["content"]
                return {
                    "summary_text": summary_text,
                    "source": "AI_GENERATED (LLM)",
                }
        except Exception as e:
            if current_app:
                current_app.logger.warning(f"LLM API Summary failed: {e}. Using deterministic factual fallback.")

    # Deterministic factual fallback summary
    summary_text = _generate_deterministic_summary(patient_data, lab_results, histories)
    return {
        "summary_text": summary_text,
        "source": "AI_GENERATED (Structured Factual Engine)",
    }

def _generate_deterministic_summary(patient, lab_results, histories):
    """
    Creates an accurate, strictly factual, patient-friendly summary without any medical judgment.
    """
    lines = []
    name = patient.get("name") or "Patient"
    pid = patient.get("patient_id") or "N/A"
    age = patient.get("age")
    sex = patient.get("sex")

    demo_str = f"**Patient Overview:** {name} (ID: {pid})"
    if age and sex:
        demo_str += f", {age}-year-old {sex}."
    elif age:
        demo_str += f", Age: {age}."
    elif sex:
        demo_str += f", Sex: {sex}."
    lines.append(demo_str)
    lines.append("")

    # Clinical Context (User Provided)
    conds = patient.get("conditions")
    meds = patient.get("medications")
    allergies = patient.get("allergies")
    symptoms = patient.get("symptoms")

    lines.append("**Recorded Clinical Information (Source: User Provided):**")
    if symptoms:
        lines.append(f"- **Current Symptoms:** {symptoms}")
    if conds:
        lines.append(f"- **Existing Medical Conditions:** {conds}")
    if meds:
        lines.append(f"- **Current Medications:** {meds}")
    if allergies:
        lines.append(f"- **Allergies:** {allergies}")
    if not (symptoms or conds or meds or allergies):
        lines.append("- No preexisting conditions, allergies, or medications entered.")
    lines.append("")

    # Laboratory Results (Extracted from Report)
    lines.append("**Laboratory Findings (Source: Extracted from Report):**")
    if not lab_results:
        lines.append("- No laboratory tests currently on file for this patient.")
    else:
        normal_tests = []
        low_tests = []
        high_tests = []
        undetermined_tests = []
        needs_verify = []

        for l in lab_results:
            t_name = l.get("test_name")
            val = l.get("value") if l.get("value") is not None else l.get("raw_value_str")
            unit = l.get("unit") or ""
            ref = l.get("reference_range") or "Not provided"
            status = (l.get("status") or "").upper()

            item_str = f"{t_name}: {val} {unit} (Reference Range: {ref})"

            if l.get("verification_required"):
                needs_verify.append(item_str)
            elif status == "LOW":
                low_tests.append(item_str)
            elif status == "HIGH":
                high_tests.append(item_str)
            elif status == "NORMAL":
                normal_tests.append(item_str)
            else:
                undetermined_tests.append(item_str)

        if low_tests:
            lines.append("- **Values Below Report Reference Range:**")
            for t in low_tests:
                lines.append(f"  • {t}")

        if high_tests:
            lines.append("- **Values Above Report Reference Range:**")
            for t in high_tests:
                lines.append(f"  • {t}")

        if normal_tests:
            lines.append(f"- **Values Within Report Reference Range ({len(normal_tests)} tests):**")
            for t in normal_tests:
                lines.append(f"  • {t}")

        if undetermined_tests:
            lines.append(f"- **Tests Without Stated Report Reference Range ({len(undetermined_tests)} tests):**")
            for t in undetermined_tests:
                lines.append(f"  • {t}")

        if needs_verify:
            lines.append(f"- **Tests Flagged for Human Verification ({len(needs_verify)} tests):**")
            for t in needs_verify:
                lines.append(f"  • {t}")

    lines.append("")
    lines.append("> **Notice & Medical Disclaimer:** This summary is an automated informational compilation strictly organizing data provided in records. It does not provide medical diagnosis, disease prediction, treatment plans, or prescriptions. All laboratory comparisons are based solely on reference ranges printed on the original report.")

    return "\n".join(lines)
