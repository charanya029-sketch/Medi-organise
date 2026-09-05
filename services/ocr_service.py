import os
import shutil
from pathlib import Path
import pytesseract
from pytesseract import Output
from PIL import Image

def find_tesseract_binary(custom_path=None):
    candidates = []
    if custom_path and str(custom_path).strip():
        candidates.append(Path(custom_path))

    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        candidates.append(Path(local_app_data) / "Programs" / "Tesseract-OCR" / "tesseract.exe")
    
    candidates.extend([
        Path(r"C:\Users\chara\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ])

    which_path = shutil.which("tesseract")
    if which_path:
        candidates.append(Path(which_path))

    for c in candidates:
        if c.is_file():
            tessdata = c.parent / "tessdata"
            if tessdata.is_dir() and "TESSDATA_PREFIX" not in os.environ:
                os.environ["TESSDATA_PREFIX"] = str(tessdata)
            return str(c)

    return None

def run_ocr(image_path_or_dict, custom_tesseract_path=None):
    """
    Executes multi-pass OCR on preprocessed image variants.
    Pass 1: PSM 6 (tabular layout preservation) on enhanced image.
    Pass 2: PSM 3 (standard segmentation) on Otsu threshold if needed.
    """
    tess_exe = find_tesseract_binary(custom_tesseract_path)
    if tess_exe:
        pytesseract.pytesseract.tesseract_cmd = tess_exe

    if isinstance(image_path_or_dict, dict):
        primary_img_path = image_path_or_dict.get("primary_processed_path")
        secondary_img_path = image_path_or_dict.get("otsu_path")
    else:
        primary_img_path = str(image_path_or_dict)
        secondary_img_path = None

    if not Path(primary_img_path).exists():
        raise FileNotFoundError(f"Image for OCR does not exist: {primary_img_path}")

    # Pass 1: Run with PSM 6 (uniform table / line layout)
    pass1_res = _execute_single_ocr(primary_img_path, config="--psm 6")

    # Pass 2: Run with PSM 3 on secondary image if confidence is low
    if (pass1_res["confidence"] < 65 or len(pass1_res["raw_text"].strip()) < 30) and secondary_img_path:
        if Path(secondary_img_path).exists():
            pass2_res = _execute_single_ocr(secondary_img_path, config="--psm 3")
            if pass2_res["confidence"] > pass1_res["confidence"]:
                pass2_res["pass_used"] = "Pass 2 (Otsu PSM 3)"
                return pass2_res

    pass1_res["pass_used"] = "Pass 1 (Enhanced PSM 6)"
    return pass1_res

def _execute_single_ocr(image_path, config=""):
    img = Image.open(image_path)
    
    data = pytesseract.image_to_data(img, output_type=Output.DICT, config=config)
    raw_text = pytesseract.image_to_string(img, config=config)

    confidences = []
    recognized_words = []
    n_boxes = len(data["text"])

    for i in range(n_boxes):
        text = data["text"][i].strip()
        conf = float(data["conf"][i])
        if text and conf >= 0:
            confidences.append(conf)
            recognized_words.append({
                "text": text,
                "confidence": conf,
                "left": data["left"][i],
                "top": data["top"][i],
                "width": data["width"][i],
                "height": data["height"][i],
            })

    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

    if avg_conf >= 75:
        confidence_label = "High"
    elif avg_conf >= 50:
        confidence_label = "Medium"
    else:
        confidence_label = "Low"

    return {
        "raw_text": raw_text,
        "confidence": round(avg_conf, 1),
        "confidence_label": confidence_label,
        "word_count": len(recognized_words),
        "words": recognized_words,
        "lines": [line.strip() for line in raw_text.splitlines() if line.strip()]
    }
