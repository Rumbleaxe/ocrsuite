# OCRSuite

Local document digitization. Vision LLMs via Ollama. No cloud, no API keys.

Extracts text, math formulas, tables, and figures from PDF scans. Outputs Markdown, LaTeX, and PNG.

---

## Install

```
git clone https://github.com/Rumbleaxe/OCRSuite.git
cd ocrsuite
uv sync
```

Requires Python 3.12+ and [Ollama](https://ollama.ai). Pull the model once:

```
ollama pull deepseek-ocr
```

## Use

```
uv run ocrsuite process --input book.pdf --output ./output/
uv run ocrsuite-gui
```

## Architecture

```
PDF → Preprocessor → OCR (DeepSeek-OCR) → Assembler → Post-process* → Output
```

\* Optional. Canny edge detection + Llava for figure-to-ASCII art, Markdown enrichment.

## Docs

| Document | Content |
|---|---|
| [SPECIFICATION.md](SPECIFICATION.md) | Full technical spec — architecture, model selection rationale, constraints |
| [AUDIT_REPORT.md](AUDIT_REPORT.md) | End-to-end audit — 42 pages, 92.9% success rate, detailed findings |
| [QUICKSTART.md](QUICKSTART.md) | 5-minute setup guide |
| [docs/OUTPUT_FORMAT_GUIDE.md](docs/OUTPUT_FORMAT_GUIDE.md) | Output structure and formats |
| [docs/LOGGING.md](docs/LOGGING.md) | ISO 8601 structured logging with loguru |
| [docs/MODELFILE.md](docs/MODELFILE.md) | Optimized DeepSeek-OCR Modelfile |
| [DeepSeekOCR_Guide.md](DeepSeekOCR_Guide.md) | DeepSeek-OCR setup and configuration |
| [AgenticAIFlowForOCR_Guide.md](AgenticAIFlowForOCR_Guide.md) | Agentic AI integration patterns for OCR |
| [LLMS.txt](LLMS.txt) | LLM-friendly project context |

## Quality

41 tests · 57% coverage · ruff · mypy · pyproject.toml

```
uv run pytest
uv run ruff check src tests
uv run mypy src
```

## License

MIT
