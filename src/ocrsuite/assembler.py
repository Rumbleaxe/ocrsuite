"""Output assembly and file generation."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .utils import ExtractionError, ensure_directory

logger = logging.getLogger(__name__)


class OutputAssembler:
    """Assemble extracted content into output files."""

    def __init__(self, output_dir: Path, source_filename: str = "document", debug: bool = False):
        """Initialize assembler.

        Args:
            output_dir: Directory for output files.
            source_filename: Original filename (without extension) for naming outputs.
            debug: If True, save intermediate data.
        """
        self.output_dir = ensure_directory(output_dir)
        self.source_filename = source_filename
        self.debug = debug
        self.timestamp = datetime.now().strftime("%d%m%y_%H%M%S")
        self.figures_dir = None
        self.metadata: dict[str, Any] = {
            "created": datetime.now().isoformat(),
            "pages_processed": 0,
            "errors": [],
        }

    def save_markdown(
        self,
        content: str,
        filename: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Path:
        """Save content as single Markdown file with linked figures.

        Args:
            content: Markdown content with figure references.
            filename: Output filename (default: DDMMYY_HHMMSS_sourcename.md).
            title: Document title for header.

        Returns:
            Path to saved file.

        Raises:
            ExtractionError: If save fails.
        """
        try:
            if filename is None:
                filename = f"{self.timestamp}_{self.source_filename}.md"

            # Build markdown with header
            md_lines = []
            if title:
                md_lines.append(f"# {title}\n")
                md_lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
            
            md_lines.append(content)

            # Add metadata section at end
            if self.metadata["errors"]:
                md_lines.append("\n---\n")
                md_lines.append("## Processing Notes\n")
                md_lines.append(f"- Pages processed: {self.metadata['pages_processed']}\n")
                md_lines.append(f"- Errors: {len(self.metadata['errors'])}\n")
                for error in self.metadata["errors"]:
                    md_lines.append(f"  - {error}\n")

            full_content = "".join(md_lines)

            output_path = self.output_dir / filename
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(full_content)

            logger.info(f"Saved Markdown to {output_path}")
            return output_path

        except Exception as e:
            raise ExtractionError(f"Failed to save Markdown file: {e}") from e

    def save_image(self, image_path: Path, destination_filename: str) -> Path:
        """Copy image to figures directory.

        Args:
            image_path: Path to source image.
            destination_filename: Filename in figures directory.

        Returns:
            Path to copied file (relative to output_dir).

        Raises:
            ExtractionError: If copy fails.
        """
        try:
            if not image_path.exists():
                raise ExtractionError(f"Source image not found: {image_path}")

            # Create figures directory if needed
            if self.figures_dir is None:
                self.figures_dir = self.output_dir / f"{self.timestamp}_{self.source_filename}"
                ensure_directory(self.figures_dir)

            output_path = self.figures_dir / destination_filename
            with open(image_path, "rb") as src:
                with open(output_path, "wb") as dst:
                    dst.write(src.read())

            logger.debug(f"Saved image to {output_path}")
            # Return relative path for markdown linking
            return Path(output_path.name).parent / output_path.name

        except Exception as e:
            raise ExtractionError(f"Failed to save image: {e}") from e

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

    def get_output_filename(self) -> str:
        """Get the output markdown filename.

        Returns:
            Filename in format DDMMYY_HHMMSS_sourcename.md
        """
        return f"{self.timestamp}_{self.source_filename}.md"

    def get_figures_dirname(self) -> str:
        """Get the figures directory name.

        Returns:
            Directory name in format DDMMYY_HHMMSS_sourcename/
        """
        return f"{self.timestamp}_{self.source_filename}"
