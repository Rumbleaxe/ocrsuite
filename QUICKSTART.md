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

# Install OCRSuite with uv
uv sync
```

## CLI

```powershell
# Process a PDF
ocrsuite process --input mybook.pdf --output ./output/

# With post-processing (ASCII art + Markdown enrichment)
ocrsuite process --input mybook.pdf --output ./output/ --postprocess

# Verbose mode for debugging
ocrsuite process --input mybook.pdf -v
```

## GUI

```powershell
# Browser interface
ocrsuite-gui

# Desktop window
ocrsuite-gui --native
```

Open `http://localhost:8080` in your browser. Upload a PDF, configure settings, and press Process.

## Output

```
output/
├── 120726_114530_mybook.md           # Raw OCR extraction
├── postprocessed_120726_114530_mybook.md  # Enriched with tables, links, ASCII art
├── 120726_114530_mybook/             # Extracted figures
│   ├── fig_001.png
│   └── ...
└── log.txt                           # ISO 8601 structured log
```

## Troubleshooting

### "Could not connect to Ollama"
```powershell
ollama serve          # Start Ollama
```

### "Model not found"
```powershell
ollama pull deepseek-ocr    # Primary model
ollama pull llava:13b        # Post-processing model
```

### Poor OCR quality
- Increase DPI: `ocrsuite process --config ocrsuite.yaml` with `dpi: 400`
- Try a different model: `--model llava:13b`
- Enable debug mode for intermediate images: set `debug_mode: true` in config

## Development

```powershell
uv sync --all-extras    # Dev dependencies
pytest                   # Run tests (41 passing)
ruff format . && ruff check . --fix && mypy src   # Code quality
```

See [README.md](README.md) for full documentation and [SPECIFICATION.md](SPECIFICATION.md) for architecture details.
