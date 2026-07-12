"""Tests for output assembler module."""

from pathlib import Path

import pytest

from ocrsuite.assembler import OutputAssembler


def test_save_markdown(temp_output_dir):
    assembler = OutputAssembler(temp_output_dir, source_filename="testdoc")
    content = "# Title\n\nSome extracted text."
    path = assembler.save_markdown(content, title="Test Document")

    assert path.exists()
    assert path.suffix == ".md"
    text = path.read_text(encoding="utf-8")
    assert "# Test Document" in text
    assert "Some extracted text" in text


def test_save_markdown_custom_filename(temp_output_dir):
    assembler = OutputAssembler(temp_output_dir, source_filename="testdoc")
    path = assembler.save_markdown("Hello", filename="custom.md")

    assert path.name == "custom.md"
    assert path.read_text(encoding="utf-8") == "Hello"


def test_record_error(temp_output_dir):
    assembler = OutputAssembler(temp_output_dir)
    assembler.record_error("Something went wrong")

    assert len(assembler.metadata["errors"]) == 1
    assert "Something went wrong" in assembler.metadata["errors"][0]


def test_increment_pages(temp_output_dir):
    assembler = OutputAssembler(temp_output_dir)
    assert assembler.metadata["pages_processed"] == 0

    assembler.increment_pages()
    assert assembler.metadata["pages_processed"] == 1

    assembler.increment_pages(5)
    assert assembler.metadata["pages_processed"] == 6


def test_get_output_filename(temp_output_dir):
    assembler = OutputAssembler(temp_output_dir, source_filename="mydoc")
    name = assembler.get_output_filename()

    assert name.endswith("_mydoc.md")
    assert len(name) > 10  # timestamp prefix


def test_get_figures_dirname(temp_output_dir):
    assembler = OutputAssembler(temp_output_dir, source_filename="mydoc")
    dirname = assembler.get_figures_dirname()

    assert dirname.endswith("_mydoc")
    assert len(dirname) > 5


def test_save_image(sample_image, temp_output_dir):
    assembler = OutputAssembler(temp_output_dir, source_filename="testdoc")
    dest = assembler.save_image(sample_image, "fig_01.png")

    assert dest is not None
    assert assembler.figures_dir is not None
    assert assembler.figures_dir.exists()
    saved = assembler.figures_dir / "fig_01.png"
    assert saved.exists()
