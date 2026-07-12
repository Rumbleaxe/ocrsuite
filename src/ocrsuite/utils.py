"""Utilities: logging configuration, error handling, and common operations."""

import sys
from datetime import datetime
from pathlib import Path

from loguru import logger


def init_logging(output_dir: Path, verbose: bool = False) -> Path:
    """Configure loguru for OCRSuite with ISO 8601 timestamps.

    Sets up dual output: file (full detail) and stderr (colorized, concise).
    Returns the path to the log file.
    """
    output_dir = ensure_directory(output_dir)
    log_file = output_dir / "log.txt"

    logger.remove()
    level = "DEBUG" if verbose else "INFO"

    logger.add(
        log_file,
        level="DEBUG",
        format="{time:YYYY-MM-DDTHH:mm:ss.SSS!UTC} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8",
    )

    logger.add(
        sys.stderr,
        level=level,
        format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | {message}",
        colorize=True,
    )

    logger.info("=" * 80)
    logger.info(f"OCRSuite — logging started ({datetime.now().isoformat()})")
    logger.info(f"Level: {level} | File: {log_file}")
    logger.info("=" * 80)

    return log_file


class OCRSuiteError(Exception):
    pass


class ConfigError(OCRSuiteError):
    pass


class PreprocessingError(OCRSuiteError):
    pass


class OllamaError(OCRSuiteError):
    pass


class ExtractionError(OCRSuiteError):
    pass


def ensure_directory(path: Path) -> Path:
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except OSError as e:
        raise OCRSuiteError(f"Failed to create directory {path}: {e}") from e
