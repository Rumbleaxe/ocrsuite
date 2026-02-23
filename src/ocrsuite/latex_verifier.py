"""LaTeX verification and compilation utilities."""

import logging
import subprocess
from pathlib import Path
from typing import Optional

from pylatexenc.latex2text import LatexNodes2Text

logger = logging.getLogger(__name__)


class LaTeXVerifier:
    """Verify and compile LaTeX documents."""

    def __init__(self):
        """Initialize verifier."""
        self.has_pdflatex = self._check_pdflatex()
        self.has_tectonic = self._check_tectonic()

    def _check_pdflatex(self) -> bool:
        """Check if pdflatex is available."""
        try:
            result = subprocess.run(
                ["pdflatex", "--version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _check_tectonic(self) -> bool:
        """Check if tectonic is available."""
        try:
            result = subprocess.run(
                ["tectonic", "--version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def validate_latex_syntax(self, tex_path: Path) -> tuple[bool, list[str]]:
        """Validate LaTeX file syntax.

        Args:
            tex_path: Path to .tex file.

        Returns:
            Tuple of (is_valid, errors).
        """
        errors = []

        if not tex_path.exists():
            errors.append(f"File not found: {tex_path}")
            return False, errors

        try:
            with open(tex_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Basic syntax checks
            if not content.startswith("\\documentclass"):
                errors.append("Missing \\documentclass declaration")

            if "\\begin{document}" not in content:
                errors.append("Missing \\begin{document}")

            if "\\end{document}" not in content:
                errors.append("Missing \\end{document}")

            # Check for unmatched braces
            open_braces = content.count("{") - content.count("}")
            if open_braces != 0:
                errors.append(f"Unmatched braces (difference: {open_braces})")

            # Check for unmatched brackets
            open_brackets = content.count("[") - content.count("]")
            if open_brackets != 0:
                errors.append(f"Unmatched brackets (difference: {open_brackets})")

            # Try to extract text content
            try:
                converter = LatexNodes2Text()
                text_content = converter.latex_to_text(content)
                if not text_content.strip():
                    logger.debug("Document appears to have no extractable text content")
            except Exception as e:
                logger.debug(f"Could not extract text content: {e}")

            return len(errors) == 0, errors

        except Exception as e:
            errors.append(f"Error reading file: {e}")
            return False, errors

    def compile_to_pdf(
        self, tex_path: Path, output_path: Optional[Path] = None
    ) -> tuple[bool, str]:
        """Compile LaTeX file to PDF.

        Args:
            tex_path: Path to .tex file.
            output_path: Path for output PDF (optional).

        Returns:
            Tuple of (success, message).
        """
        if not tex_path.exists():
            return False, f"File not found: {tex_path}"

        if not output_path:
            output_path = tex_path.parent / tex_path.stem / ".pdf"

        # Try tectonic first (better for CI/CD, no dependencies)
        if self.has_tectonic:
            try:
                logger.info(f"Compiling with Tectonic: {tex_path}")
                result = subprocess.run(
                    ["tectonic", str(tex_path), "-o", str(output_path.parent)],
                    capture_output=True,
                    timeout=60,
                    text=True,
                )
                if result.returncode == 0:
                    logger.info(f"Successfully compiled to {output_path}")
                    return True, f"Compiled to {output_path}"
                else:
                    return False, f"Tectonic error: {result.stderr}"
            except subprocess.TimeoutExpired:
                return False, "Tectonic compilation timed out"
            except Exception as e:
                logger.warning(f"Tectonic compilation failed: {e}")

        # Try pdflatex as fallback
        if self.has_pdflatex:
            try:
                logger.info(f"Compiling with pdflatex: {tex_path}")
                result = subprocess.run(
                    [
                        "pdflatex",
                        "-interaction=nonstopmode",
                        f"-output-directory={output_path.parent}",
                        str(tex_path),
                    ],
                    capture_output=True,
                    timeout=60,
                    text=True,
                )
                if result.returncode == 0:
                    logger.info(f"Successfully compiled to {output_path}")
                    return True, f"Compiled to {output_path}"
                else:
                    return False, f"pdflatex error: {result.stderr}"
            except subprocess.TimeoutExpired:
                return False, "pdflatex compilation timed out"
            except Exception as e:
                logger.warning(f"pdflatex compilation failed: {e}")

        # No compiler available
        return False, (
            "No LaTeX compiler found. Install Tectonic or pdflatex for PDF compilation."
        )

    def get_status(self) -> str:
        """Get verification status message.

        Returns:
            Status message describing available compilers.
        """
        msg = "LaTeX Verification Status:\n"
        if self.has_tectonic:
            msg += "  ✓ Tectonic (recommended)\n"
        if self.has_pdflatex:
            msg += "  ✓ pdflatex\n"
        if not self.has_tectonic and not self.has_pdflatex:
            msg += "  ✗ No LaTeX compiler installed\n"
            msg += "     For PDF compilation, install:\n"
            msg += "       - Tectonic: https://tectonic-typesetting.github.io/\n"
            msg += "       - Or MiKTeX/pdflatex\n"

        return msg
