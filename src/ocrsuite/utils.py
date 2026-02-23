"""Utilities for logging, error handling, and common operations."""

import logging
from datetime import datetime
from pathlib import Path


def setup_logging(output_dir: Path, verbose: bool = False) -> Path:
    """Configure comprehensive logging for OCRSuite.

    Sets up both console and file logging with structured output.

    Args:
        output_dir: Directory where log file will be written.
        verbose: If True, use DEBUG level; otherwise INFO.

    Returns:
        Path to the log file.
    """
    # Ensure output directory exists
    output_dir = ensure_directory(output_dir)
    log_file = output_dir / "log.txt"

    level = logging.DEBUG if verbose else logging.INFO

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # File handler - detailed logging
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # Always capture debug to file
    file_formatter = logging.Formatter(
        "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)

    # Console handler - concise output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        "%(levelname)s | %(message)s"
    )
    console_handler.setFormatter(console_formatter)

    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Log initialization
    logger = logging.getLogger("ocrsuite")
    logger.info("=" * 80)
    logger.info(f"OCRSuite Logging Started - {datetime.now().isoformat()}")
    logger.info(f"Log Level: {logging.getLevelName(level)}")
    logger.info(f"Log File: {log_file}")
    logger.info("=" * 80)

    return log_file


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
