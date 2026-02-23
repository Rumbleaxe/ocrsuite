"""PDF preprocessing and image conversion."""

import logging
from pathlib import Path
from typing import List

import pdfplumber
from PIL import Image

from .utils import PreprocessingError, ensure_directory

logger = logging.getLogger(__name__)


class PDFPreprocessor:
    """Convert PDF pages to high-resolution images."""

    def __init__(self, dpi: int = 300):
        """Initialize preprocessor.

        Args:
            dpi: Resolution for image conversion.
        """
        self.dpi = dpi
        self.scale = dpi / 72.0  # Convert points to pixels

    def pdf_to_images(
        self, pdf_path: Path, output_dir: Path, max_pages: int | None = None
    ) -> List[Path]:
        """Convert PDF pages to PNG images.

        Args:
            pdf_path: Path to input PDF file.
            output_dir: Directory for output images.
            max_pages: Maximum pages to convert (None for all).

        Returns:
            List of paths to generated image files.

        Raises:
            PreprocessingError: If PDF processing fails.
        """
        if not pdf_path.exists():
            raise PreprocessingError(f"PDF file not found: {pdf_path}")

        ensure_directory(output_dir)
        image_paths = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                pages_to_process = (
                    min(max_pages, total_pages) if max_pages else total_pages
                )

                logger.info(f"Converting {pages_to_process} pages from {pdf_path.name}")

                for page_num, page in enumerate(pdf.pages[:pages_to_process]):
                    try:
                        # Render page as image
                        image = page.to_image(resolution=self.dpi).original

                        # Save image
                        output_path = output_dir / f"page_{page_num + 1:04d}.png"
                        image.save(output_path, "PNG")
                        image_paths.append(output_path)

                        logger.debug(
                            f"Processed page {page_num + 1}/{pages_to_process}"
                        )

                    except Exception as e:
                        logger.warning(
                            f"Failed to process page {page_num + 1}: {e}"
                        )
                        continue

                logger.info(
                    f"Successfully converted {len(image_paths)}/{pages_to_process} pages"
                )

        except Exception as e:
            raise PreprocessingError(f"PDF processing failed: {e}") from e

        return image_paths

    def get_pdf_info(self, pdf_path: Path) -> dict:
        """Extract PDF metadata.

        Args:
            pdf_path: Path to PDF file.

        Returns:
            Dictionary with page count and metadata.

        Raises:
            PreprocessingError: If PDF processing fails.
        """
        if not pdf_path.exists():
            raise PreprocessingError(f"PDF file not found: {pdf_path}")

        try:
            with pdfplumber.open(pdf_path) as pdf:
                return {
                    "page_count": len(pdf.pages),
                    "metadata": pdf.metadata or {},
                }
        except Exception as e:
            raise PreprocessingError(f"Failed to read PDF info: {e}") from e
