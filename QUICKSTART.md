# OCRSuite Quick Start

Get OCRSuite running in 5 minutes.

## Prerequisites

- Python 3.12+
- [Ollama](https://ollama.ai)

## Install

```powershell
git clone https://github.com/Rumbleaxe/OCRSuite.git
cd ocrsuite

# Start Ollama (keep running in a separate terminal)
ollama serve

# Pull the OCR model
ollama pull deepseek-ocr

# Optionally: pull Llava for post-processing
ollama pull llava:13b

# Install dependencies
uv sync                     # For CLI + GUI
uv sync --all-extras        # Includes dev tools (pytest, ruff, mypy)
```

## Run

All commands use `uv run` from the project root:

```powershell
# CLI — process a PDF
uv run ocrsuite process --input mybook.pdf --output ./output/

# CLI — with post-processing
uv run ocrsuite process --input mybook.pdf --output ./output/ --postprocess

# GUI — browser at http://localhost:8080
uv run ocrsuite-gui

# GUI — desktop window
uv run ocrsuite-gui --native

# Run tests
uv run pytest
```

Without `uv`, install globally first:
```powershell
pip install -e .
ocrsuite process --input mybook.pdf
ocrsuite-gui
```

## Output

```
output/
├── 120726_114530_mybook.md
├── postprocessed_120726_114530_mybook.md
├── 120726_114530_mybook/
│   └── fig_*.png
└── log.txt
```

## Troubleshooting

### "Could not connect to Ollama"
```powershell
ollama serve
```

### "Model not found"
```powershell
ollama pull deepseek-ocr
ollama pull llava:13b
```

### Poor OCR quality
- Increase DPI: `dpi: 400` in config
- Try a different model: `--model llava:13b`
- Enable debug mode for intermediate images

## Development

```powershell
uv sync --all-extras
uv run pytest
uv run ruff format . && uv run ruff check . --fix && uv run mypy src
```

See [README.md](README.md) for full documentation.
