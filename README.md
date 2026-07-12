# OCRSuite

**AI-powered PDF processing for digitizing old books** using Ollama vision models and open-source tools.

OCRSuite extracts text, math formulas, tables, and figures from PDF scans of historical documents, outputting:
- **LaTeX (.tex)** – Text and mathematical formulas in LaTeX format
- **PNG files** – Extracted figures and diagrams
- **Markdown (.md)** – Tables in Markdown format

## Key Features

- **Fully Local** — No cloud dependencies. All processing runs on your machine via Ollama.
- **AI-Powered** — Leverages vision models (DeepSeek-OCR, Llama 3.2 Vision) for accurate OCR on degraded text.
- **Math & Layout Aware** — Handles complex layouts, mathematical notation, and illustrations from old books.
- **Minimal Dependencies** — Designed for Windows with only essential libraries.
- **Modular Pipeline** — Each stage (PDF → images → OCR → extraction) is independently testable.

## Requirements

- **Python 3.12+**
- **Ollama** ([ollama.ai](https://ollama.ai)) – Running locally with at least one vision model
- **Windows 10/11** (or Linux/macOS with minor adjustments)

## Quick Start

### 1. Install Ollama

Download from [ollama.ai](https://ollama.ai) and run:

```powershell
ollama serve
```

In a new terminal, pull a vision model:

```powershell
ollama pull llama2-vision
# or
ollama pull deepseek-coder-v2
```

### 2. Install OCRSuite

```powershell
# Clone the repository
git clone https://github.com/Rumbleaxe/OCRSuite.git
cd ocrsuite

# Install with uv (recommended) or pip
uv sync
# or: pip install -e ".[dev]"
```

### 3. Process a PDF

```powershell
ocrsuite process --input book.pdf --output ./output/
```

This will:
1. Convert PDF pages to high-resolution images
2. Send to Ollama for OCR and content classification
3. Extract text/math to LaTeX, figures to PNG, tables to Markdown
4. Save all outputs to `./output/`

## Usage

### Command-Line Interface

```powershell
# Full options
ocrsuite process \
  --input input.pdf \
  --output ./output \
  --model llama2-vision \
  --config config.yaml \
  --verbose

# With configuration file
ocrsuite process --input book.pdf --config ocrsuite.yaml
```

### Configuration File (YAML)

Create `ocrsuite.yaml`:

```yaml
pdf:
  dpi: 300  # Resolution for image conversion
  
ollama:
  url: "http://localhost:11434"
  model: "llama2-vision"
  timeout: 120
  
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
```

## Architecture

OCRSuite follows a modular pipeline:

```
PDF Input
  ↓
[Preprocessor] → Convert to high-res images
  ↓
[Ollama OCR] → Extract text, identify math/tables/figures
  ↓
[Extractors] → Parse into specialized formats
  ↓
[Assembler] → Write LaTeX, PNG, Markdown files
  ↓
Output Directory
```

### Core Modules

- **`preprocessor.py`** – PDF → images (pdfplumber + Pillow)
- **`ollama_client.py`** – Ollama API wrapper with retry logic
- **`extractor.py`** – Parse Ollama responses into structured data
- **`assembler.py`** – Write LaTeX, PNG, Markdown outputs
- **`config.py`** – Load and validate configuration
- **`main.py`** – CLI entry point (Typer)

## Development

### Setup Development Environment

```powershell
# Install with dev dependencies
uv sync --all-extras

# Or with pip
pip install -e ".[dev]"
```

### Run Tests

```powershell
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test
pytest tests/test_preprocessor.py::test_pdf_to_images
```

### Code Quality

```powershell
# Format code
ruff format src tests

# Lint
ruff check src tests --fix

# Type checking
mypy src

# All at once
ruff format . && ruff check . --fix && mypy src
```

## Project Structure

```
ocrsuite/
├── src/ocrsuite/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── config.py            # Config loading/validation
│   ├── preprocessor.py      # PDF → images
│   ├── ollama_client.py     # Ollama API integration
│   ├── extractor.py         # Parse OCR results
│   ├── assembler.py         # Output generation
│   └── utils.py             # Logging, error handling
├── tests/
│   ├── __init__.py
│   ├── test_preprocessor.py
│   ├── test_ollama_client.py
│   └── resources/           # Sample PDFs for testing
├── .github/
│   ├── copilot-instructions.md
│   └── workflows/           # CI/CD workflows
├── docs/
├── pyproject.toml           # Project metadata and dependencies
├── LICENSE                  # MIT License
├── README.md                # This file
├── SPECIFICATION.md         # Architecture and design docs
└── LLMS.txt                 # Agentic AI integration guidelines
```

## Technologies

| Component | Tool | Why |
|-----------|------|-----|
| PDF Processing | `pdfplumber` | Lightweight, pure Python, Windows-native |
| Images | `Pillow` | Standard, minimal footprint |
| HTTP Requests | `requests` | Simple, reliable |
| CLI | `Typer` | Modern, type-safe, beautiful help |
| Configuration | `PyYAML` | Standard for config files |
| OCR / AI | Ollama | Local vision models, no cloud |
| Testing | `pytest` | Industry standard |
| Code Quality | `ruff` | Fast, all-in-one (format, lint, type-check) |

## Troubleshooting

### Ollama Connection Failed

**Error:** `Could not connect to Ollama at http://localhost:11434`

**Solution:**
1. Ensure Ollama is running: `ollama serve` in a terminal
2. Check if running on different port: Update `ocrsuite.yaml` or use `--ollama-url http://localhost:PORT`

### Out of Memory

**Error:** Model inference fails with OOM errors

**Solution:**
1. Use a smaller model: `ollama pull llama2-vision` (7B instead of 13B)
2. Process fewer pages at once
3. Increase system swap/pagefile

### Poor OCR Quality on Old Books

**Tips:**
- Increase DPI in config: `dpi: 400` or higher
- Try different model: DeepSeek-OCR vs. Llama 3.2
- Check PDF page quality; preprocessing may help

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Implement with tests
4. Run code quality checks: `ruff format . && ruff check . --fix && mypy src`
5. Submit a pull request

See `SPECIFICATION.md` for architecture details and `LLMS.txt` for AI integration guidelines.

## License

MIT License – see [LICENSE](LICENSE) file.

## Resources

- [Ollama Models](https://ollama.ai) – Download vision models
- [pdfplumber Documentation](https://github.com/jamesturk/pdfplumber)
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Project Specification](SPECIFICATION.md)

## Roadmap

- [x] MVP: Basic PDF → LaTeX/PNG/MD extraction
- [ ] Batch processing multiple PDFs
- [ ] Improved math formula detection
- [ ] Custom model support
- [ ] Web UI (Streamlit)
- [ ] Performance optimizations
- [ ] Docker deployment guide

## Citation

If you use OCRSuite in research, please cite:

```bibtex
@software{ocrsuite2026,
  author = {OCRSuite Contributors},
  title = {OCRSuite: AI-powered PDF Processing for Old Books},
  url = {https://github.com/Rumbleaxe/OCRSuite},
  year = {2026}
}
```

## Contact

Questions or feedback? Open an issue on GitHub or contact the maintainers.

---

MIT License. See [LICENSE](LICENSE).
