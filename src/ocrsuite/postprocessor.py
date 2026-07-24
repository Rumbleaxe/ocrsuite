"""Post-processing pipeline: Llava vision enrichment for OCR output.

Converts extracted Markdown and figures into enhanced output:
- Text sections: Llava identifies tables, links, lists → valid Markdown
- Figures: Canny edge detection → Llava → ASCII art code blocks
"""

import tempfile
from pathlib import Path

import cv2
from loguru import logger

from .ollama_client import OllamaClient

DEFAULT_ASCII_WIDTH = 80
DEFAULT_CANNY_LOW = 50
DEFAULT_CANNY_HIGH = 150
MAX_TEXT_CHARS = 4000  # context window safety margin


class PostProcessor:
    """Llava vision-model enrichment of OCRSuite output."""

    def __init__(
        self,
        client: OllamaClient,
        ascii_width: int = DEFAULT_ASCII_WIDTH,
        canny_low: int = DEFAULT_CANNY_LOW,
        canny_high: int = DEFAULT_CANNY_HIGH,
    ):
        self.client = client
        self.ascii_width = ascii_width
        self.canny_low = canny_low
        self.canny_high = canny_high

    def enrich_markdown(self, raw_text: str) -> str:
        """Ask Llava to identify and apply Markdown formatting to raw OCR text.

        Sends text content (no image) to Llava for structural analysis.
        Returns the enriched Markdown, or the original text on failure.
        """
        prompt = (
            "Analyze this OCR-extracted text. Identify any elements that "
            "should be formatted with Markdown syntax: "
            "tables (use | columns with --- headers), "
            "headings (use # ## ###), "
            "bullet lists (use -), "
            "numbered lists (use 1. 2.), "
            "code blocks (use ```), "
            "blockquotes (use >), "
            "and hyperlinks. "
            "Return the full text with proper Markdown. "
            "Preserve ALL original content — only ADD formatting, never remove text."
        )

        text_chunk = raw_text[:MAX_TEXT_CHARS]
        try:
            result = self.client.generate_text(f"{prompt}\n\nText:\n{text_chunk}")
            return result if result.strip() else raw_text
        except Exception as e:
            logger.warning(f"Markdown enrichment failed: {e}")
            return raw_text

    def figure_to_ascii(self, image_path: Path) -> str:
        """Convert a figure image to ASCII art via Canny edge detection + Llava.

        1. Load grayscale image
        2. Apply Canny edge detection
        3. Send edge image to Llava for ASCII art generation
        4. Return as a Markdown fenced code block

        Falls back to a Markdown image reference on failure.
        """
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            logger.warning(f"Cannot read image: {image_path}")
            return f"![Figure]({image_path.name})"

        edges = cv2.Canny(img, self.canny_low, self.canny_high)

        edge_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
                edge_path = Path(tf.name)
                cv2.imwrite(str(edge_path), edges)

            prompt = (
                f"Describe this edge-detected diagram or figure as ASCII art. "
                f"Use box-drawing characters (╔ ═ ╗ ║ ╚ ╝ ╠ ╬ ╣), "
                f"lines, arrows, and text characters. "
                f"Max width: {self.ascii_width} columns. "
                f"Output ONLY the ASCII art with no explanation."
            )
            ascii_art = self.client.ocr_image(edge_path, prompt=prompt)
            return (
                f"```\n{ascii_art}\n```" if ascii_art.strip() else f"![Figure]({image_path.name})"
            )

        except Exception as e:
            logger.warning(f"ASCII art conversion failed for {image_path.name}: {e}")
            return f"![Figure]({image_path.name})"
        finally:
            if edge_path and edge_path.exists():
                try:
                    edge_path.unlink()
                except Exception:
                    pass

    def postprocess(self, md_path: Path, figures_dir: Path) -> str:
        """Run full post-processing on OCR output.

        Reads the raw extraction Markdown, enriches with Llava text analysis,
        and replaces figure references with ASCII art.

        Returns enriched Markdown string.
        """
        content = md_path.read_text(encoding="utf-8")

        logger.info("Post-processing: enriching Markdown structure")
        try:
            content = self.enrich_markdown(content)
        except Exception as e:
            logger.warning(f"Markdown enrichment skipped: {e}")

        if figures_dir and figures_dir.exists():
            png_files = sorted(figures_dir.glob("*.png"))
            for png_file in png_files:
                logger.info(f"Post-processing figure: {png_file.name}")
                ascii_block = self.figure_to_ascii(png_file)
                ref = f"![Figure]({png_file.name})"
                if ref not in content:
                    ref = png_file.name
                content = content.replace(ref, ascii_block)

        return content
