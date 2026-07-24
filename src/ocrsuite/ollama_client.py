"""Ollama integration for OCR and content recognition."""

import base64
import time
from pathlib import Path

import requests
from loguru import logger

from .config import OllamaConfig
from .utils import OllamaError


class OllamaClient:
    """Client for Ollama vision model integration."""

    def __init__(self, config: OllamaConfig):
        self.url = config.url.rstrip("/")
        self.model = config.model
        self.timeout = config.timeout
        self.max_retries = config.max_retries

    def health_check(self) -> bool:
        try:
            response = requests.get(f"{self.url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def ocr_image(self, image_path: Path, prompt: str = "") -> str:
        if not image_path.exists():
            raise OllamaError(f"Image not found: {image_path}")

        if not prompt:
            prompt = "Free OCR."

        return self._call_vision_model(image_path, prompt)

    def classify_content(self, image_path: Path) -> dict[str, str | float]:
        prompt = "<|grounding|>Given the layout of the image."
        response = self._call_vision_model(image_path, prompt).strip().lower()

        valid_types = {"text", "table", "figure", "mixed", "unknown"}
        content_type = "unknown"

        if response in valid_types:
            content_type = response
        else:
            for word in response.split():
                word = word.strip(".,!?;:'\"").lower()
                if word in valid_types:
                    content_type = word
                    logger.debug(f"Extracted '{word}' from response: '{response}'")
                    break

        return {"type": content_type, "confidence": 0.8}

    def extract_math(self, image_path: Path) -> str:
        prompt = (
            "Extract all mathematical formulas from this image and "
            "convert them to LaTeX format. "
            "Use $...$ for inline math and $$...$$ for display math. "
            "Include any surrounding text that helps context."
        )
        return self._call_vision_model(image_path, prompt)

    def extract_table(self, image_path: Path) -> str:
        prompt = (
            "Extract the table from this image and convert it to "
            "Markdown format. "
            "Use | separators for columns and - for header rows. "
            "Preserve all data accurately."
        )
        return self._call_vision_model(image_path, prompt)

    def generate_text(self, prompt: str) -> str:
        """Send a text-only prompt (no image) to the model."""
        try:
            response = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=self.timeout,
            )
            if response.status_code != 200:
                raise OllamaError(f"Ollama returned status {response.status_code}: {response.text}")
            data = response.json()
            return str(data.get("response", "")).strip()
        except requests.ConnectionError as e:
            raise OllamaError(
                f"Could not connect to Ollama at {self.url}. Is it running? Try: ollama serve"
            ) from e
        except requests.Timeout as e:
            raise OllamaError(f"Ollama request timed out after {self.timeout}s") from e
        except Exception as e:
            raise OllamaError(f"Ollama API call failed: {e}") from e

    def _call_vision_model(self, image_path: Path, prompt: str, retry: int = 0) -> str:
        try:
            image_data = self._encode_image(image_path)

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
                raise OllamaError(f"Ollama returned status {response.status_code}: {response.text}")

            data = response.json()
            result = data.get("response", "")
            return str(result).strip()

        except requests.ConnectionError as e:
            if retry < self.max_retries:
                wait_time = 2**retry
                logger.warning(
                    f"Connection failed, retrying in {wait_time}s "
                    f"(attempt {retry + 1}/{self.max_retries})"
                )
                time.sleep(wait_time)
                return self._call_vision_model(image_path, prompt, retry + 1)
            raise OllamaError(
                f"Could not connect to Ollama at {self.url}. Is it running? Try: ollama serve"
            ) from e

        except requests.Timeout as e:
            raise OllamaError(f"Ollama request timed out after {self.timeout}s") from e

        except Exception as e:
            raise OllamaError(f"Ollama API call failed: {e}") from e

    @staticmethod
    def _encode_image(image_path: Path) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
