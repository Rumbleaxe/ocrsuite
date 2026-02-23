"""Tests for LaTeX verification module."""

import tempfile
from pathlib import Path

import pytest

from ocrsuite.latex_verifier import LaTeXVerifier


def test_latex_verifier_initialization():
    """Test LaTeX verifier initialization."""
    verifier = LaTeXVerifier()
    assert verifier is not None
    # Check methods exist
    assert hasattr(verifier, "validate_latex_syntax")
    assert hasattr(verifier, "compile_to_pdf")


def test_validate_valid_latex():
    """Test validation of valid LaTeX."""
    verifier = LaTeXVerifier()
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_file = Path(tmpdir) / "test.tex"
        tex_file.write_text(
            "\\documentclass{article}\n"
            "\\begin{document}\n"
            "Hello, World!\n"
            "\\end{document}\n"
        )
        is_valid, errors = verifier.validate_latex_syntax(tex_file)
        assert is_valid, f"LaTeX validation failed with errors: {errors}"
        assert len(errors) == 0


def test_validate_missing_documentclass():
    """Test validation detects missing documentclass."""
    verifier = LaTeXVerifier()
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_file = Path(tmpdir) / "test.tex"
        tex_file.write_text(
            r"""
\begin{document}
Hello
\end{document}
"""
        )
        is_valid, errors = verifier.validate_latex_syntax(tex_file)
        assert not is_valid
        assert any("documentclass" in e.lower() for e in errors)


def test_validate_unmatched_braces():
    """Test validation detects unmatched braces."""
    verifier = LaTeXVerifier()
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_file = Path(tmpdir) / "test.tex"
        tex_file.write_text(
            r"""
\documentclass{article}
\begin{document}
Hello {world
\end{document}
"""
        )
        is_valid, errors = verifier.validate_latex_syntax(tex_file)
        assert not is_valid
        assert any("brace" in e.lower() for e in errors)


def test_validate_missing_file():
    """Test validation of non-existent file."""
    verifier = LaTeXVerifier()
    is_valid, errors = verifier.validate_latex_syntax(Path("/nonexistent/file.tex"))
    assert not is_valid
    assert any("not found" in e.lower() for e in errors)


def test_get_status():
    """Test status message generation."""
    verifier = LaTeXVerifier()
    status = verifier.get_status()
    assert "LaTeX Verification Status" in status
    assert len(status) > 0
