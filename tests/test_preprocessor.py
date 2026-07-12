"""Tests for preprocessing module."""

from pathlib import Path

import pytest

from ocrsuite.preprocessor import PDFPreprocessor
from ocrsuite.utils import PreprocessingError


def test_preprocessor_init():
    preprocessor = PDFPreprocessor(dpi=300)
    assert preprocessor.dpi == 300
    assert preprocessor.scale == 300 / 72.0


def test_pdf_not_found():
    preprocessor = PDFPreprocessor()
    with pytest.raises(PreprocessingError):
        preprocessor.pdf_to_images(Path("nonexistent.pdf"), Path("."))


def test_pdf_to_images_output_directory_created(tmp_path):
    preprocessor = PDFPreprocessor()
    output_dir = tmp_path / "new_dir"
    assert not output_dir.exists()

    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    try:
        preprocessor.pdf_to_images(pdf_path, output_dir)
    except PreprocessingError:
        pass

    assert output_dir.exists()


def test_get_pdf_info(sample_pdf):
    preprocessor = PDFPreprocessor()
    info = preprocessor.get_pdf_info(sample_pdf)

    assert "page_count" in info
    assert info["page_count"] >= 0
    assert "metadata" in info


def test_pdf_to_images_with_sample(sample_pdf, tmp_path):
    preprocessor = PDFPreprocessor(dpi=72)
    output_dir = tmp_path / "images"

    images = preprocessor.pdf_to_images(sample_pdf, output_dir)
    assert len(images) > 0
    for img in images:
        assert img.exists()
        assert img.suffix == ".png"
