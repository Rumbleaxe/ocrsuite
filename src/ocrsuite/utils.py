"""Utilities for logging, error handling, and common operations."""

import logging
from pathlib import Path


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for OCRSuite.

    Args:
        verbose: If True, use DEBUG level; otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


class OCRSuiteError(Exception):
    """Base exception for OCRSuite errors."""

    pass


class ConfigError(OCRSuiteError):
    """Configuration-related error."""

    pass


class PreprocessingError(OCRSuiteError):
    """PDF preprocessing error."""

    pass


class OllamaError(OCRSuiteError):
    """Ollama integration error."""

    pass


class ExtractionError(OCRSuiteError):
    """Content extraction error."""

    pass


def ensure_directory(path: Path) -> Path:
    """Ensure directory exists, creating if necessary.

    Args:
        path: Directory path.

    Returns:
        The path.

    Raises:
        OSError: If directory creation fails.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except OSError as e:
        raise OCRSuiteError(f"Failed to create directory {path}: {e}") from e
