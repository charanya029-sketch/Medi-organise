import pytest
from pathlib import Path
from services.image_preprocessing import preprocess_medical_image

def test_preprocessing_pipeline(tmp_path):
    """Verifies that the OpenCV preprocessing pipeline executes all steps and saves artifacts."""
    sample_img = Path(__file__).resolve().parent.parent / "static" / "images" / "sample_reports" / "sample_cbc_report.png"
    assert sample_img.exists(), "Sample image must exist for testing"

    out_dir = tmp_path / "preprocessed_test"
    result = preprocess_medical_image(sample_img, output_dir=out_dir)

    assert "original_path" in result
    assert "primary_processed_path" in result
    assert "otsu_path" in result
    assert "adaptive_path" in result
    assert Path(result["primary_processed_path"]).exists()
    assert Path(result["otsu_path"]).exists()
    assert Path(result["adaptive_path"]).exists()
    assert result["scale_factor"] >= 1.0
