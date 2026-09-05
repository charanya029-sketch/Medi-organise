import os
import cv2
import numpy as np
from PIL import Image
from pathlib import Path

def preprocess_medical_image(input_path, output_dir=None):
    """
    Complete image preprocessing pipeline according to Section 8:
    Original -> Resize/Upscale -> Grayscale -> Denoising -> Contrast Enhancement (CLAHE)
    -> Sharpening -> Thresholding -> Deskewing -> Multi-pass variants.
    
    Retains original image untouched. Returns dict of saved artifact paths and preprocessed images.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input image not found: {input_path}")

    if output_dir is None:
        output_dir = input_path.parent / "preprocessed"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Handle PDF conversion if needed
    if input_path.suffix.lower() == ".pdf":
        converted_img_path = _convert_pdf_first_page_to_image(input_path, output_dir)
        input_image_path = converted_img_path
    else:
        input_image_path = input_path

    # Read image using OpenCV
    img = cv2.imread(str(input_image_path))
    if img is None:
        # Fallback to PIL if cv2 cannot open non-ASCII or specific formats
        pil_img = Image.open(str(input_image_path)).convert("RGB")
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    h, w = img.shape[:2]

    # 1. Resize / Upscale (Upscale low-resolution scans to boost OCR accuracy)
    scale_factor = 1.0
    if w < 1600 or h < 1600:
        scale_factor = max(1600.0 / max(w, 1), 1600.0 / max(h, 1))
        # Cap scaling at 3x to avoid excessive memory
        scale_factor = min(scale_factor, 3.0)
        new_w = int(w * scale_factor)
        new_h = int(h * scale_factor)
        upscaled = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    else:
        upscaled = img.copy()

    # 2. Grayscale Conversion
    gray = cv2.cvtColor(upscaled, cv2.COLOR_BGR2GRAY)

    # 3. Denoising (Bilateral Filter preserves crisp text edges while smoothing background paper noise)
    denoised = cv2.bilateralFilter(gray, d=7, sigmaColor=75, sigmaSpace=75)

    # 4. Contrast Enhancement via CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast_enhanced = clahe.apply(denoised)

    # 5. Sharpening (Unsharp Mask filter to accentuate text strokes)
    gaussian_blur = cv2.GaussianBlur(contrast_enhanced, (0, 0), 2.0)
    sharpened = cv2.addWeighted(contrast_enhanced, 1.5, gaussian_blur, -0.5, 0)

    # 6. Thresholding: Primary Otsu Binarization + Secondary Adaptive Gaussian
    _, otsu_thresh = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    adaptive_thresh = cv2.adaptiveThreshold(
        sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 11
    )

    # 7. Deskewing (Detect text orientation angle and rotate)
    deskewed_gray, deskew_angle = _deskew_image(sharpened)
    deskewed_otsu, _ = _deskew_image(otsu_thresh, known_angle=deskew_angle)

    # Save artifacts for verification and multi-pass OCR
    stem = input_path.stem
    primary_processed_path = output_dir / f"{stem}_preprocessed.png"
    otsu_path = output_dir / f"{stem}_otsu.png"
    adaptive_path = output_dir / f"{stem}_adaptive.png"

    cv2.imwrite(str(primary_processed_path), deskewed_gray)
    cv2.imwrite(str(otsu_path), deskewed_otsu)
    cv2.imwrite(str(adaptive_path), adaptive_thresh)

    return {
        "original_path": str(input_path),
        "primary_processed_path": str(primary_processed_path),
        "otsu_path": str(otsu_path),
        "adaptive_path": str(adaptive_path),
        "scale_factor": scale_factor,
        "deskew_angle": round(deskew_angle, 2),
    }

def _deskew_image(image, known_angle=None):
    """
    Estimates text skew angle and rotates the image to upright alignment.
    """
    if known_angle is not None:
        angle = known_angle
    else:
        # Binarize temporarily to detect contour angles
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        inv = cv2.bitwise_not(gray)
        _, thresh = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) < 50:
            angle = 0.0
        else:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            elif angle > 45:
                angle = 90 - angle
            else:
                angle = -angle

    # If angle is minor (< 0.5 degrees), avoid unnecessary interpolation
    if abs(angle) < 0.5 or abs(angle) > 45:
        return image, 0.0

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image, rot_mat, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )
    return rotated, angle

def _convert_pdf_first_page_to_image(pdf_path, output_dir):
    """
    Converts the first page of a PDF file to a PNG image for OCR processing.
    Uses pypdf image extraction or render fallback.
    """
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    if len(reader.pages) == 0:
        raise ValueError("PDF has no pages")
    
    first_page = reader.pages[0]
    out_img_path = output_dir / f"{pdf_path.stem}_page1.png"

    # Extract embedded image if available
    images = getattr(first_page, "images", [])
    if images and len(images) > 0:
        img_obj = images[0]
        with open(out_img_path, "wb") as f:
            f.write(img_obj.data)
        return out_img_path

    # Synthetic render fallback from text content if no raw raster image is embedded
    text_content = first_page.extract_text() or "Empty PDF Document"
    blank = Image.new("RGB", (1200, 1600), color=(255, 255, 255))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(blank)
    y = 50
    for line in text_content.splitlines()[:50]:
        draw.text((50, y), line, fill=(0, 0, 0))
        y += 28
    blank.save(out_img_path)
    return out_img_path
