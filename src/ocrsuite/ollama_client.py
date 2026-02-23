"""Ollama integration for OCR and content recognition."""

import base64
import logging
import time
from pathlib import Path
from typing import Optional

import requests
from PIL import Image

from .config import OllamaConfig
from .utils import OllamaError

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for Ollama vision model integration."""

    def __init__(self, config: OllamaConfig):
        """Initialize Ollama client.

        Args:
            config: Ollama configuration.
        """
        self.url = config.url.rstrip("/")
        self.model = config.model
        self.timeout = config.timeout
        self.max_retries = config.max_retries

    def health_check(self) -> bool:
        """Check if Ollama server is running.

        Returns:
            True if server is healthy.
        """
        try:
            response = requests.get(f"{self.url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    def ocr_image(self, image_path: Path, prompt: str = "") -> str:
        """Extract text from an image using OCR.

        Args:
            image_path: Path to image file.
            prompt: Custom prompt for OCR.

        Returns:
            Extracted text.

        Raises:
            OllamaError: If OCR fails.
        """
        if not image_path.exists():
            raise OllamaError(f"Image not found: {image_path}")

        if not prompt:
            prompt = (
                "Extract all text from this image. "
                "Preserve formatting and structure. "
                "For mathematical formulas, use LaTeX notation "
                "(e.g., $x^2 + y^2 = z^2$). "
                "For tables, describe the structure clearly."
            )

        return self._call_vision_model(image_path, prompt)

    def classify_content(self, image_path: Path) -> dict[str, str | float]:
        """Classify image content (text, table, figure, math).

        Args:
            image_path: Path to image file.

        Returns:
            Dictionary with 'type' and 'confidence' keys.
            Type can be: 'text', 'table', 'figure', 'mixed', 'unknown'

        Raises:
            OllamaError: If classification fails.
        """
        prompt = (
            "Classify the primary content in this image. "
            "Respond with ONLY one of these categories:\n"
            "- text: Contains mainly readable text\n"
            "- table: Contains a data table or matrix\n"
            "- figure: Contains a diagram, chart, or illustration\n"
            "- mixed: Contains multiple types of content\n"
            "- unknown: Cannot determine content type\n\n"
            "Respond with the category name only."
        )

        response = self._call_vision_model(image_path, prompt).strip().lower()

        # Map response to valid category
        valid_types = {"text", "table", "figure", "mixed", "unknown"}
        content_type = response if response in valid_types else "unknown"

        return {"type": content_type, "confidence": 0.8}

    def extract_math(self, image_path: Path) -> str:
        """Extract mathematical formulas from image.

        Args:
            image_path: Path to image file.

        Returns:
            Mathematical content in LaTeX format.

        Raises:
            OllamaError: If extraction fails.
        """
        prompt = (
            "Extract all mathematical formulas from this image and "
            "convert them to LaTeX format. "
            "Use $...$ for inline math and $$...$$ for display math. "
            "Include any surrounding text that helps context."
        )

        return self._call_vision_model(image_path, prompt)

    def extract_table(self, image_path: Path) -> str:
        """Extract table from image as Markdown.

        Args:
            image_path: Path to image file.

        Returns:
            Table in Markdown format.

        Raises:
            OllamaError: If extraction fails.
        """
        prompt = (
            "Extract the table from this image and convert it to "
            "Markdown format. "
            "Use | separators for columns and - for header rows. "
            "Preserve all data accurately."
        )

        return self._call_vision_model(image_path, prompt)

    def _call_vision_model(
        self, image_path: Path, prompt: str, retry: int = 0
    ) -> str:
        """Call Ollama vision model with retry logic.

        Args:
            image_path: Path to image file.
            prompt: Prompt for the model.
            retry: Current retry attempt.

        Returns:
            Model response.

        Raises:
            OllamaError: If all retries fail.
        """
        try:
            # Encode image as base64
            image_data = self._encode_image(image_path)

            # Call Ollama API
            response = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "images": [image_data],
                    "stream": False,
                },
                timeout=self.timeout,
            )

            if response.status_code != 200:
                raise OllamaError(
                    f"Ollama returned status {response.status_code}: "
                    f"{response.text}"
                )

            return response.json().get("response", "").strip()

        except requests.ConnectionError as e:
            if retry < self.max_retries:
                wait_time = 2 ** retry
                logger.warning(
                    f"Connection failed, retrying in {wait_time}s "
                    f"(attempt {retry + 1}/{self.max_retries})"
                )
                time.sleep(wait_time)
                return self._call_vision_model(image_path, prompt, retry + 1)
            raise OllamaError(
                f"Could not connect to Ollama at {self.url}. "
                "Is it running? Try: ollama serve"
            ) from e

        except requests.Timeout as e:
            raise OllamaError(
                f"Ollama request timed out after {self.timeout}s"
            ) from e

        except Exception as e:
            raise OllamaError(f"Ollama API call failed: {e}") from e

    @staticmethod
    def _encode_image(image_path: Path) -> str:
        """Encode image as base64 for API transmission.

        Args:
            image_path: Path to image file.

        Returns:
            Base64-encoded image string.
        """
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
