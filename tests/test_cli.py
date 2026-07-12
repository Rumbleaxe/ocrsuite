"""Tests for CLI entry point."""

from typer.testing import CliRunner

from ocrsuite.main import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "process" in result.stdout
    assert "version" in result.stdout


def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "OCRSuite" in result.stdout


def test_cli_process_missing_input():
    result = runner.invoke(app, ["process", "--help"])
    assert result.exit_code == 0
    assert "--input" in result.stdout


def test_cli_process_no_input():
    result = runner.invoke(app, ["process"])
    assert result.exit_code != 0
