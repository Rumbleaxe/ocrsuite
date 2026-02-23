"""Configuration loading and validation."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class PDFConfig:
    """PDF processing configuration."""

    dpi: int = 300
    max_pages: Optional[int] = None


@dataclass
class OllamaConfig:
    """Ollama integration configuration."""

    url: str = "http://localhost:11434"
    model: str = "llama2-vision"
    timeout: int = 120
    max_retries: int = 3


@dataclass
class OCRConfig:
    """OCR and extraction configuration."""

    confidence_threshold: float = 0.5
    extract_math: bool = True
    extract_tables: bool = True
    extract_figures: bool = True


@dataclass
class OutputConfig:
    """Output format configuration."""

    format_latex: bool = True
    format_markdown: bool = True
    extract_images: bool = True
    debug_mode: bool = False


@dataclass
class Config:
    """Main configuration container."""

    pdf: PDFConfig = field(default_factory=PDFConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    ocr: OCRConfig = field(default_factory=OCRConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @classmethod
    def from_file(cls, path: Path) -> "Config":
        """Load configuration from YAML file.

        Args:
            path: Path to YAML config file.

        Returns:
            Config instance with loaded settings.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If YAML parsing fails.
        """
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}

        return cls(
            pdf=PDFConfig(**data.get("pdf", {})),
            ollama=OllamaConfig(**data.get("ollama", {})),
            ocr=OCRConfig(**data.get("ocr", {})),
            output=OutputConfig(**data.get("output", {})),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        """Create config from dictionary.

        Args:
            data: Dictionary with config sections.

        Returns:
            Config instance.
        """
        return cls(
            pdf=PDFConfig(**data.get("pdf", {})),
            ollama=OllamaConfig(**data.get("ollama", {})),
            ocr=OCRConfig(**data.get("ocr", {})),
            output=OutputConfig(**data.get("output", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary.

        Returns:
            Configuration as dictionary.
        """
        return {
            "pdf": {
                "dpi": self.pdf.dpi,
                "max_pages": self.pdf.max_pages,
            },
            "ollama": {
                "url": self.ollama.url,
                "model": self.ollama.model,
                "timeout": self.ollama.timeout,
                "max_retries": self.ollama.max_retries,
            },
            "ocr": {
                "confidence_threshold": self.ocr.confidence_threshold,
                "extract_math": self.ocr.extract_math,
                "extract_tables": self.ocr.extract_tables,
                "extract_figures": self.ocr.extract_figures,
            },
            "output": {
                "format_latex": self.output.format_latex,
                "format_markdown": self.output.format_markdown,
                "extract_images": self.output.extract_images,
                "debug_mode": self.output.debug_mode,
            },
        }
