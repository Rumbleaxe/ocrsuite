"""Tests for post-processing module."""

import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from ocrsuite.config import OllamaConfig
from ocrsuite.ollama_client import OllamaClient
from ocrsuite.postprocessor import PostProcessor


@pytest.fixture
def pp_client():
    cfg = OllamaConfig(url="http://localhost:11434", model="llava:13b")
    return OllamaClient(cfg)


@pytest.fixture
def processor(pp_client):
    return PostProcessor(pp_client)


def test_canny_edge_detect_creates_output(sample_image, tmp_path):
    """Verify Canny edge detection produces a non-blank result."""
    img = cv2.imread(str(sample_image), cv2.IMREAD_GRAYSCALE)
    assert img is not None

    edges = cv2.Canny(img, 50, 150)
    out_path = tmp_path / "edges.png"
    cv2.imwrite(str(out_path), edges)

    assert out_path.exists()
    assert out_path.stat().st_size > 0


def test_canny_defaults(processor):
    assert processor.canny_low == 50
    assert processor.canny_high == 150
    assert processor.ascii_width == 80


def test_enrich_markdown_passthrough(processor, mocker):
    """When Llava fails, original text is returned unchanged."""
    mocker.patch.object(processor.client, "generate_text", side_effect=Exception("fail"))
    original = "# Header\nSome text\nMore text"
    result = processor.enrich_markdown(original)
    assert result == original


def test_enrich_markdown_success(processor, mocker):
    """When Llava succeeds, the enriched text is returned."""
    mocker.patch.object(
        processor.client,
        "generate_text",
        return_value="# Enriched\n- item 1\n- item 2",
    )
    result = processor.enrich_markdown("raw text")
    assert "Enriched" in result
    assert "item 1" in result


def test_figure_to_ascii_invalid_path(processor):
    result = processor.figure_to_ascii(Path("/nonexistent/figure.png"))
    assert result.startswith("![Figure]")


def test_postprocess_empty_figures_dir(tmp_path, processor, mocker):
    """Postprocess with no figures should still enrich markdown."""
    md_path = tmp_path / "doc.md"
    md_path.write_text("# Doc\nSimple text.", encoding="utf-8")

    mocker.patch.object(
        processor.client,
        "generate_text",
        return_value="# Doc\nSimple text.\n- bullet",
    )

    figures_dir = tmp_path / "figures"
    figures_dir.mkdir()

    result = processor.postprocess(md_path, figures_dir)
    assert "bullet" in result
