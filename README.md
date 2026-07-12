# OCRSuite

**Local document digitization pipeline.** Vision LLMs via Ollama. No cloud. No API keys.

OCRSuite extracts text, math formulas, tables, and figures from PDF scans. Post-processing enriches the output with tables, links, and ASCII art via a secondary vision model.

Output: Markdown, LaTeX, PNG figures.

## Key Features

- **Fully local** — No network beyond localhost. All processing on your machine.
- **DeepSeek-OCR** — Token-efficient OCR via custom Modelfile. 97% precision at <10x compression ratio.
- **Dual interface** — CLI (`ocrsuite process`) and desktop GUI (`ocrsuite-gui`).
- **Modular pipeline** — Preprocess → OCR → Assemble → (optional) Post-process.
- **Post-processing** — Canny edge detection + Llava for figure-to-ASCII art. Tables, links, and lists detected and rendered as valid Markdown.
- **ISO 8601 logging** — Structured logs via loguru with rotation and retention.
- **Test coverage** — 41 tests, 57% coverage (excluding GUI).

## Requirements

- Python 3.12+
- [Ollama](https://ollama.ai) running locally
- DeepSeek-OCR model pulled. Llava optional for post-processing.

## Installation

```powershell
git clone https://github.com/Rumbleaxe/OCRSuite.git
cd ocrsuite

# Install with uv (recommended)
uv sync

# Pull the OCR model and build the optimized variant
ollama pull deepseek-ocr
```

OCRSuite auto-builds `ocrsuite-deepseek` from the Modelfile on first use.

## Launching

All commands via `uv run` from the project root:

```
uv run ocrsuite        CLI (below)
uv run ocrsuite-gui    Desktop + web GUI
uv run pytest           Run tests
```

Without `uv`, install globally:

```
pip install -e .
ocrsuite process --input book.pdf
ocrsuite-gui
```

## CLI Usage

```powershell
# Basic processing
uv run ocrsuite process --input book.pdf --output ./output/

# With custom model, DPI, and verbose logging
uv run ocrsuite process --input book.pdf --model llava:13b --dpi 400 --verbose

# With post-processing (tables, links, ASCII art from figures)
uv run ocrsuite process --input book.pdf --output ./output/ --postprocess --postprocess-model llava:13b

# Process only first 10 pages with debug mode
uv run ocrsuite process --input book.pdf --max-pages 10 --verbose
```

### Full options

```
ocrsuite process
  --input PATH          PDF file (required)
  --output PATH         Output directory (default: ./output)
  --model MODEL         Ollama model (default: ocrsuite-deepseek)
  --max-pages N         Process first N pages only
  --config PATH         YAML config file
  --verbose / -v        Debug-level logging
  --postprocess         Enable vision model post-processing
  --postprocess-model M Vision model for enrichment (default: llava:13b)
```

## GUI

```powershell
uv run ocrsuite-gui              # Browser at http://localhost:8080
uv run ocrsuite-gui --native     # Desktop window
```

Features:
- Drag-and-drop or click-to-upload PDF
- Live progress: phase indicators, page-by-page OCR timer, bottleneck finder
- Ollama health check with status badge
- Configurable model, DPI, max pages, debug mode
- Post-processing toggle with vision model selector (Advanced section)
- Download output files directly from the UI
- "View Log" button during processing

## Architecture

```
PDF Input
  ↓
[Preprocessor]     pdfplumber → high-res PNG images
  ↓
[OllamaClient]     DeepSeek-OCR via Ollama API (retry logic, health checks)
  ↓
[Assembler]        Markdown + LaTeX + PNG figures
  ↓
[PostProcessor]*   Canny edge detect → Llava vision → ASCII art + Markdown enrichment
  ↓
Output Directory   extraction.md, postprocessed.md, figures/*.png
```

\* Optional. Enabled via `--postprocess` flag or GUI toggle.

## Core Modules

| Module | Role |
|---|---|
| `preprocessor.py` | PDF → images (pdfplumber + Pillow) |
| `ollama_client.py` | Ollama API: OCR, classification, text generation |
| `assembler.py` | Output generation: Markdown, LaTeX, figures |
| `postprocessor.py` | Llava enrichment: Canny edges → ASCII art, Markdown formatting |
| `config.py` | YAML config loading, typed dataclasses |
| `main.py` | CLI entry point (Typer + Rich progress) |
| `gui.py` | Desktop/web UI (NiceGUI, async pipeline) |
| `utils.py` | Loguru configuration, error classes |

## Configuration

```yaml
pdf:
  dpi: 300
  max_pages: null

ollama:
  url: "http://localhost:11434"
  model: "ocrsuite-deepseek"
  timeout: 600
  max_retries: 3

ocr:
  confidence_threshold: 0.5
  extract_math: true
  extract_tables: true
  extract_figures: true

output:
  format_latex: true
  format_markdown: true
  extract_images: true
  debug_mode: false

postprocess:
  enabled: false
  model: "llava:13b"
  ascii_width: 80
  canny_low: 50
  canny_high: 150
```

## Technologies

| Component | Tool | Role |
|---|---|---|
| PDF | pdfplumber | Page rendering, metadata |
| Vision | Ollama (DeepSeek-OCR, Llava) | OCR and figure analysis |
| Post-processing | OpenCV (Canny) | Edge detection for ASCII art |
| CLI | Typer + Rich | Command line with progress bars |
| GUI | NiceGUI | Web + native desktop interface |
| Logging | loguru | ISO 8601, rotation, retention |
| Testing | pytest + pytest-mock + pytest-cov | 41 tests, 57% coverage |
| Quality | ruff + mypy | Lint, format, type check |

## Development

```powershell
uv sync --all-extras       # Install with dev dependencies
uv run pytest               # Run all tests
uv run pytest --cov=src     # With coverage report
uv run ruff format src tests  # Format
uv run ruff check src tests   # Lint
uv run mypy src               # Type check
```

## Troubleshooting

### Ollama not running
```powershell
ollama serve              # Start in a separate terminal
```

### Model not found
```powershell
ollama pull deepseek-ocr  # Primary OCR model
ollama pull llava:13b     # For post-processing (optional)
```

### "Free OCR." prompt sensitive to input

DeepSeek-OCR uses a command DSL. OCRSuite sends `Free OCR.` as the default. Classification uses `<|grounding|>Given the layout of the image.` Missing punctuation or newlines may degrade output. See [Ollama DeepSeek-OCR docs](https://ollama.com/library/deepseek-ocr) for the full command reference.

### Slow processing

- Reduce DPI (150-200 for drafts)
- Limit pages with `--max-pages`
- Use a smaller model (7B vs 13B)
- Close GPU-intensive applications

## Roadmap

- [x] MVP: PDF → Markdown/LaTeX/PNG extraction
- [x] Desktop/web GUI with live progress
- [x] Post-processing: ASCII art + Markdown enrichment
- [x] ISO 8601 loguru logging
- [ ] Batch processing
- [ ] Docker deployment
- [ ] CI/CD via GitHub Actions

## License

MIT. See [LICENSE](LICENSE).
