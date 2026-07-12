"""Shared fixtures for OCRSuite tests."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """Create a minimal valid PDF for pipeline tests."""
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\n"
        b"startxref\n190\n%%EOF\n"
    )
    return pdf_path


@pytest.fixture
def sample_image(tmp_path: Path) -> Path:
    """Create a small test PNG image readable by OpenCV."""
    img_path = tmp_path / "test.png"
    import numpy as np

    # Create a 10x10 white image and encode as PNG
    img = np.full((10, 10, 3), 255, dtype=np.uint8)
    import cv2
    cv2.imwrite(str(img_path), img)
    return img_path


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Temporary output directory that is guaranteed to be empty."""
    out = tmp_path / "output"
    out.mkdir()
    return out
