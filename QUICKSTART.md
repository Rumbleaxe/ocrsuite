# OCRSuite Quick Start Guide

Get OCRSuite running in 5 minutes on Windows.

## Prerequisites

- **Python 3.12+** (Download from [python.org](https://www.python.org))
- **Ollama** (Download from [ollama.ai](https://ollama.ai))

## Installation

### 1. Clone the Repository

```powershell
git clone https://github.com/yourusername/ocrsuite.git
cd ocrsuite
```

### 2. Start Ollama

In a PowerShell terminal, start the Ollama server:

```powershell
ollama serve
```

You should see:
```
Serving on 127.0.0.1:11434
```

### 3. Pull a Vision Model (in a new terminal)

```powershell
# Option 1: Faster, smaller model
ollama pull llama2-vision

# Option 2: More accurate but larger
ollama pull deepseek-coder-v2

# Option 3: Lightweight
ollama pull granite-vision
```

### 4. Install OCRSuite

```powershell
# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install OCRSuite
pip install -e .
```

Or use `uv` (faster):

```powershell
uv venv .venv
.\.venv\Scripts\Activate.ps1
uv pip install -e .
```

## Usage

### Basic Processing

```powershell
ocrsuite process --input mybook.pdf --output ./output/
```

### With Configuration File

```powershell
# Copy and edit the example config
copy ocrsuite.yaml.example ocrsuite.yaml

# Use custom config
ocrsuite process --input mybook.pdf --config ocrsuite.yaml --output ./output/
```

### Command-Line Options

```powershell
ocrsuite process \
  --input book.pdf \
  --output ./results \
  --model llama2-vision \
  --max-pages 10 \
  --verbose
```

**Options:**
- `--input PATH` - PDF file to process (required)
- `--output PATH` - Output directory (default: `./output`)
- `--model MODEL` - Ollama model name (default: `llama2-vision`)
- `--config PATH` - YAML config file
- `--max-pages N` - Process only first N pages
- `--verbose` - Show detailed logs
- `--help` - Show all options

## Output

OCRSuite generates:

```
output/
├── document.tex          # LaTeX document with extracted text and math
├── extraction.md         # Markdown version with all extracted content
├── metadata.txt          # Processing metadata
└── figure_*.png          # Extracted figures (if any)
```

### LaTeX Document

The `document.tex` file is ready to compile:

```powershell
# On Windows with MiKTeX
pdflatex document.tex output.pdf

# Or use Overleaf to upload and compile online
```

## Troubleshooting

### "Could not connect to Ollama"

**Problem:** Getting error about Ollama connection.

**Solution:**
1. Ensure Ollama is running: `ollama serve` in a terminal
2. Check if using non-default port: `ollama serve --port 11434`
3. Verify with browser: http://localhost:11434/api/tags (should show JSON)

### "Model not found"

**Problem:** Error saying model doesn't exist.

**Solution:**
```powershell
# Pull the model first
ollama pull llama2-vision

# Or try a different model
ollama pull deepseek-coder-v2
```

### "Out of memory" or slow processing

**Problem:** Processing is slow or crashes with OOM.

**Solution:**
1. Use a smaller model: `ollama pull llama2-vision` (7B) instead of 13B
2. Reduce DPI in config: `dpi: 150` instead of 300
3. Process fewer pages: `--max-pages 5`
4. Increase system RAM or use WSL2 on Windows

### Poor OCR Quality

**Problem:** Extracted text has errors or missing content.

**Solutions:**
1. Try a different model: DeepSeek-OCR often better for mixed content
2. Increase DPI: `dpi: 400` or `dpi: 500` for degraded scans
3. Check PDF quality: If PDF itself is blurry, OCR will struggle
4. Use debug mode to inspect intermediate images: `debug_mode: true`

## Development

### Run Tests

```powershell
pytest
```

### Code Quality

```powershell
# Format code
ruff format src tests

# Lint
ruff check src tests

# Type checking
mypy src
```

### Run with Dev Dependencies

```powershell
pip install -e ".[dev]"
pytest --cov=src
```

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [SPECIFICATION.md](SPECIFICATION.md) for architecture details
- See [.github/copilot-instructions.md](.github/copilot-instructions.md) for development guidelines

## Support

- **Issues**: Open a GitHub issue with error logs and PDF sample (if possible)
- **Discussions**: Start a discussion for questions
- **Documentation**: Check README.md and SPECIFICATION.md

## Common Model Recommendations

| Model | Best For | Speed | Memory | Accuracy |
|-------|----------|-------|--------|----------|
| **llama2-vision** | General OCR | Medium | 8-16GB | Good |
| **deepseek-coder-v2** | Math/code/complex | Slow | 16GB+ | Excellent |
| **granite-vision** | Fast processing | Fast | 4-8GB | Fair |

Try `llama2-vision` first—it's a good balance.

---

**Ready to digitize your books!** 📚✨
