"""Tests for preprocessing module."""

import tempfile
from pathlib import Path

import pytest

from ocrsuite.preprocessor import PDFPreprocessor
from ocrsuite.utils import PreprocessingError


def test_preprocessor_init():
    """Test preprocessor initialization."""
    preprocessor = PDFPreprocessor(dpi=300)
    assert preprocessor.dpi == 300
    assert preprocessor.scale == 300 / 72.0


def test_pdf_not_found():
    """Test error handling for missing PDF."""
    preprocessor = PDFPreprocessor()
    with pytest.raises(PreprocessingError):
        preprocessor.pdf_to_images(Path("nonexistent.pdf"), Path("."))


def test_pdf_to_images_output_directory_created(tmp_path):
    """Test that output directory is created if it doesn't exist."""
    preprocessor = PDFPreprocessor()
    output_dir = tmp_path / "new_dir"
    
    assert not output_dir.exists()
    # This would fail with real PDF, but tests that directory creation works
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")  # Minimal invalid PDF
    
    try:
        preprocessor.pdf_to_images(pdf_path, output_dir)
    except PreprocessingError:
        # Expected to fail on invalid PDF, but directory should be created
        pass
    
    assert output_dir.exists()
