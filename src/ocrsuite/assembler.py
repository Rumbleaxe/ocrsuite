"""Output assembly and file generation."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .utils import ensure_directory, ExtractionError

logger = logging.getLogger(__name__)


class OutputAssembler:
    """Assemble extracted content into output files."""

    def __init__(self, output_dir: Path, debug: bool = False):
        """Initialize assembler.

        Args:
            output_dir: Directory for output files.
            debug: If True, save intermediate data.
        """
        self.output_dir = ensure_directory(output_dir)
        self.debug = debug
        self.metadata = {
            "created": datetime.now().isoformat(),
            "pages_processed": 0,
            "errors": [],
        }

    def save_latex(
        self,
        content: str,
        filename: str = "document.tex",
        title: Optional[str] = None,
        author: Optional[str] = None,
    ) -> Path:
        """Save content as LaTeX document.

        Args:
            content: LaTeX content (body).
            filename: Output filename.
            title: Document title.
            author: Document author.

        Returns:
            Path to saved file.

        Raises:
            ExtractionError: If save fails.
        """
        try:
            # Build complete LaTeX document
            preamble = self._build_latex_preamble(title, author)
            full_content = f"{preamble}\n\n\\begin{{document}}\n\n{content}\n\n\\end{{document}}\n"

            output_path = self.output_dir / filename
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(full_content)

            logger.info(f"Saved LaTeX to {output_path}")
            return output_path

        except Exception as e:
            raise ExtractionError(f"Failed to save LaTeX file: {e}") from e

    def save_markdown(self, content: str, filename: str = "tables.md") -> Path:
        """Save content as Markdown file.

        Args:
            content: Markdown content.
            filename: Output filename.

        Returns:
            Path to saved file.

        Raises:
            ExtractionError: If save fails.
        """
        try:
            output_path = self.output_dir / filename
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Saved Markdown to {output_path}")
            return output_path

        except Exception as e:
            raise ExtractionError(f"Failed to save Markdown file: {e}") from e

    def save_image(self, image_path: Path, destination_filename: str) -> Path:
        """Copy image to output directory.

        Args:
            image_path: Path to source image.
            destination_filename: Filename in output directory.

        Returns:
            Path to copied file.

        Raises:
            ExtractionError: If copy fails.
        """
        try:
            if not image_path.exists():
                raise ExtractionError(f"Source image not found: {image_path}")

            output_path = self.output_dir / destination_filename
            with open(image_path, "rb") as src:
                with open(output_path, "wb") as dst:
                    dst.write(src.read())

            logger.debug(f"Saved image to {output_path}")
            return output_path

        except Exception as e:
            raise ExtractionError(f"Failed to save image: {e}") from e

    def save_metadata(self, filename: str = "metadata.txt") -> Path:
        """Save processing metadata.

        Args:
            filename: Output filename.

        Returns:
            Path to saved metadata file.
        """
        try:
            output_path = self.output_dir / filename
            with open(output_path, "w") as f:
                f.write("OCRSuite Processing Metadata\n")
                f.write("=" * 40 + "\n\n")
                f.write(f"Created: {self.metadata['created']}\n")
                f.write(f"Pages processed: {self.metadata['pages_processed']}\n")
                if self.metadata["errors"]:
                    f.write(f"\nErrors ({len(self.metadata['errors'])}):\n")
                    for error in self.metadata["errors"]:
                        f.write(f"  - {error}\n")

            logger.debug(f"Saved metadata to {output_path}")
            return output_path

        except Exception as e:
            logger.warning(f"Failed to save metadata: {e}")
            return None

    @staticmethod
    def _build_latex_preamble(
        title: Optional[str] = None, author: Optional[str] = None
    ) -> str:
        """Build LaTeX document preamble.

        Args:
            title: Document title.
            author: Document author.

        Returns:
            LaTeX preamble string.
        """
        preamble = r"""
\documentclass[12pt]{article}
\usepackage[utf-8]{inputenc}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{graphicx}
\usepackage[margin=1in]{geometry}
"""

        if title or author:
            preamble += "\n"
            if title:
                preamble += f'\n\\title{{{title}}}\n'
            if author:
                preamble += f'\n\\author{{{author}}}\n'
            preamble += "\n\\maketitle"

        return preamble

    def record_error(self, error_msg: str) -> None:
        """Record processing error.

        Args:
            error_msg: Error description.
        """
        self.metadata["errors"].append(error_msg)
        logger.warning(f"Recorded error: {error_msg}")

    def increment_pages(self, count: int = 1) -> None:
        """Increment processed page counter.

        Args:
            count: Number of pages processed.
        """
        self.metadata["pages_processed"] += count
