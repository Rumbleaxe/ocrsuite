"""Tests for configuration module."""

import tempfile
from pathlib import Path

import pytest

from ocrsuite.config import Config


def test_config_defaults():
    """Test default configuration values."""
    config = Config()
    assert config.pdf.dpi == 300
    assert config.ollama.url == "http://localhost:11434"
    assert config.ollama.model == "llama3.2"
    assert config.ocr.confidence_threshold == 0.5


def test_config_from_dict():
    """Test creating config from dictionary."""
    data = {
        "pdf": {"dpi": 400},
        "ollama": {"model": "deepseek-ocr"},
    }
    config = Config.from_dict(data)
    assert config.pdf.dpi == 400
    assert config.ollama.model == "deepseek-ocr"
    assert config.ocr.confidence_threshold == 0.5  # Default


def test_config_to_dict():
    """Test converting config to dictionary."""
    config = Config()
    data = config.to_dict()
    assert "pdf" in data
    assert "ollama" in data
    assert "ocr" in data
    assert "output" in data


def test_config_from_yaml_file():
    """Test loading config from YAML file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        config_path.write_text(
            """
pdf:
  dpi: 400
  max_pages: 10
ollama:
  model: deepseek-ocr
  timeout: 180
ocr:
  extract_math: true
output:
  debug_mode: true
"""
        )

        config = Config.from_file(config_path)
        assert config.pdf.dpi == 400
        assert config.pdf.max_pages == 10
        assert config.ollama.model == "deepseek-ocr"
        assert config.ollama.timeout == 180
        assert config.output.debug_mode is True


def test_config_file_not_found():
    """Test error handling for missing config file."""
    with pytest.raises(FileNotFoundError):
        Config.from_file(Path("nonexistent.yaml"))
