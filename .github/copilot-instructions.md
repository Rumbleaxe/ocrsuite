# Copilot Instructions for OCRSuite

This document provides guidance for GitHub Copilot and other AI assistants working on the OCRSuite project—an AI-powered PDF processing application for digitizing old books using open-source models and Ollama.

## Project Overview

**OCRSuite** extracts and digitizes content from PDFs of old books by:
- Converting PDFs to high-resolution images
- Analyzing page layout to detect text, math formulas, tables, and figures
- Using Ollama-hosted vision models (Llama 3.2 Vision, DeepSeek-OCR) for OCR and content recognition
- Outputting LaTeX (.tex) for text/math, PNG files for figures, and Markdown (.md) for tables
- Maintaining local execution—no cloud dependencies, emphasis on privacy

See `SPECIFICATION.md` for detailed architecture and `LLMS.txt` for agentic AI integration guidelines.

## Technology Stack

- **Language**: Python 3.12+
- **Dependency Management**: Poetry (pyproject.toml)
- **Key Libraries**:
  - `pdf2image`, `PyMuPDF`: PDF to image conversion
  - `opencv-python`: Image processing and figure extraction
  - `paddleocr`: Supplementary OCR
  - `pylatex`: LaTeX document generation
  - Ollama client: Vision model integration
  - `pytest`: Testing framework
  - `black`, `isort`, `flake8`, `mypy`: Code quality
- **Runtime**: Ollama server (runs locally with GPU support for inference)

## Project Structure

```
ocrsuite/
├── .github/
│   ├── copilot-instructions.md  (this file)
│   └── workflows/               (GitHub Actions CI/CD)
├── src/ocrsuite/
│   ├── __init__.py
│   ├── main.py                  (CLI entry point)
│   ├── config.py                (YAML config, model selection)
│   ├── preprocessor.py          (PDF → images)
│   ├── layout_analyzer.py       (Layout detection via Surya/PDF-Extract-Kit)
│   ├── ocr_engine.py            (Ollama/PaddleOCR wrapper)
│   ├── math_extractor.py        (Math formula → LaTeX)
│   ├── table_converter.py       (Table recognition → Markdown)
│   ├── figure_extractor.py      (Figure isolation, save as PNG)
│   └── assembler.py             (Compile output files)
├── tests/
│   ├── __init__.py
│   ├── test_preprocessor.py
│   ├── test_ocr_engine.py
│   ├── test_math_extractor.py
│   ├── test_table_converter.py
│   └── resources/               (Sample PDFs for testing)
├── docs/
│   ├── conf.py                  (Sphinx config)
│   └── index.rst
├── .gitignore                   (Python template)
├── LICENSE
├── README.md
├── pyproject.toml               (Poetry metadata, dependencies, entry points)
├── poetry.lock                  (Locked dependency versions)
├── SPECIFICATION.md             (Detailed architecture and design)
├── LLMS.txt                     (Agentic AI integration framework)
└── Dockerfile                   (Multi-stage, for local deployment)
```

## Build, Test, and Lint Commands

### Setup Environment

```powershell
# Install Poetry
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Create virtual environment and install dependencies
poetry install --with dev

# Ensure Ollama is running (separate terminal)
ollama serve
# Pull required models
ollama pull llama3.2-vision
ollama pull deepseek-coder-v2
```

### Run Application

```powershell
# Basic usage
poetry run python src/ocrsuite/main.py --input book.pdf --output ./output/

# With custom config
poetry run python src/ocrsuite/main.py --input book.pdf --config config.yaml --output ./output/

# Show version
poetry run python src/ocrsuite/main.py --version
```

### Testing

```powershell
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_preprocessor.py

# Run single test function
poetry run pytest tests/test_preprocessor.py::test_pdf_to_images

# Run with coverage report (target 80%+)
poetry run pytest --cov=src --cov-report=html

# Run only failed tests from last run
poetry run pytest --lf
```

### Code Quality

```powershell
# Format code with Black (88 char line length)
poetry run black .

# Sort imports with isort
poetry run isort .

# Lint with flake8
poetry run flake8 src tests

# Type checking with mypy
poetry run mypy src

# Run all checks (format, sort, lint, type check)
poetry run black . && poetry run isort . && poetry run flake8 src tests && poetry run mypy src
```

### Building and Packaging

```powershell
# Build wheel and source distribution
poetry build

# Build Docker image for local deployment
docker build -t ocrsuite:latest .
docker run --gpus all -v $(pwd)/input:/input -v $(pwd)/output:/output ocrsuite:latest --input /input/book.pdf --output /output/
```

### Documentation

```powershell
# Generate Sphinx HTML documentation
poetry run sphinx-build docs docs/_build/html

# View in browser
start docs/_build/html/index.html
```

## Key Conventions and Patterns

### Code Style

- **PEP 8 Compliance**: All code must pass `black` and `isort` formatting.
- **Type Hints**: Use PEP 484 type hints on all functions and methods. Required for `mypy` compliance.
- **Docstrings**: Google or NumPy style docstrings for every class and public function.
  ```python
  def extract_text_regions(image: np.ndarray, confidence: float = 0.5) -> List[Dict]:
      """Extract text regions from page image using layout analysis.
      
      Args:
          image: High-resolution page image (300+ DPI).
          confidence: Confidence threshold for region detection (0-1).
      
      Returns:
          List of region dicts with keys: {'bbox', 'type', 'content'}.
      
      Raises:
          ValueError: If image has invalid dimensions.
      """
  ```

- **Error Handling**: Use structured exceptions (custom subclasses of `Exception`) and the `logging` module, not `print()`.
  ```python
  import logging
  
  logger = logging.getLogger(__name__)
  
  class OCREngineError(Exception):
      """Base exception for OCR engine failures."""
  
  try:
      result = ollama_client.generate(...)
  except ollama.errors.ConnectionError as e:
      logger.error(f"Ollama connection failed: {e}", exc_info=True)
      raise OCREngineError("Could not reach Ollama server") from e
  ```

### Module Organization

- **Separation of Concerns**: Each module handles one aspect of the pipeline (preprocessing, layout analysis, OCR, extraction, assembly).
- **Dependency Injection**: Pass dependencies explicitly; avoid global state.
  ```python
  class OCREngine:
      def __init__(self, model_name: str, ollama_url: str = "http://localhost:11434"):
          self.model = model_name
          self.client = ollama.Client(url=ollama_url)
  ```

- **Configuration**: Use a dataclass or YAML-based config loader (in `config.py`) for model selection, paths, and tunables. Do not hardcode these.
  ```python
  @dataclass
  class OCRConfig:
      primary_model: str = "llama3.2-vision"
      fallback_model: str = "deepseek-ocr"
      confidence_threshold: float = 0.5
      max_workers: int = 4
  ```

### Ollama Integration

- **Model Wrapping**: Encapsulate Ollama client calls in a service class for easy mocking and error handling.
  ```python
  class OllamaOCRService:
      def __init__(self, model: str):
          self.model = model
      
      def ocr_image(self, image: np.ndarray, prompt: str) -> str:
          # Convert numpy array to base64, call Ollama, return text
          pass
  ```

- **Prompts**: Use consistent, well-engineered prompts. Store as constants or config for easy tuning.
  ```python
  EXTRACT_TEXT_PROMPT = """Extract all text from this page image. 
  Convert inline math to LaTeX (e.g., \\( x^2 + y \\)).
  Preserve formatting and structure."""
  ```

- **Graceful Degradation**: If a model fails, log and fall back to an alternative (e.g., Tesseract or a lighter Ollama model).

### Testing Strategy

- **Unit Tests**: Mock Ollama calls, test layout detection logic in isolation.
  ```python
  def test_extract_text_regions(mock_layout_analyzer):
      image = np.random.randint(0, 256, (600, 800, 3), dtype=np.uint8)
      regions = extract_text_regions(image)
      assert len(regions) > 0
      assert all('bbox' in r and 'type' in r for r in regions)
  ```

- **Integration Tests**: Use sample PDFs from `tests/resources/` (e.g., degraded scans, math-heavy pages).
- **Edge Cases**: Test on scanned PDFs with low quality, large page counts, and mixed content (math, tables, figures).
- **Windows Compatibility**: Use `ThreadPoolExecutor` instead of `multiprocessing.Pool` for multiprocessing on Windows.

### Git and Commits

- **Commit Messages**: Be descriptive. Format: `<type>: <summary>` (e.g., `feat: Add LaTeX math extraction`, `fix: Handle PDF parsing errors`).
- **Atomic Commits**: Each commit should be a logical unit (one feature or bug fix).
- **Branches**: Use feature branches (e.g., `feature/math-extraction`) off `develop`; merge to `main` after testing.
- **Co-authored-by**: Include in commit messages when working with other agents/contributors.
  ```
  Fix: Handle Windows path separators in preprocessor
  
  Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
  ```

### Windows-Specific Considerations

- **Paths**: Use `os.path` or `pathlib.Path`; avoid hardcoded forward slashes.
- **Multiprocessing**: Prefer `ThreadPoolExecutor` over `multiprocessing.Pool` to avoid pickling issues.
- **GPU Support**: If using GPU with Ollama, ensure CUDA is installed; Ollama will detect and use it.
- **Tesseract**: Install via `choco install tesseract` or compile from source; configure path in `config.py`.

### Documentation and Docstrings

- Every function and class must have a docstring explaining purpose, args, returns, and exceptions.
- Use Sphinx for auto-generated HTML docs from docstrings.
- Keep README.md updated with usage examples and setup instructions.

## Agentic AI Workflow

This project is designed to be maintained by agentic AI systems (like Copilot, Claude, OpenCode). See `LLMS.txt` for detailed integration guidelines. Key points:

- **Plan-Execute-Verify Loop**: Propose changes, test in isolation, verify with full test suite before committing.
- **Small, Atomic Commits**: Each commit should be focused and pass all tests.
- **Sandbox Experimentation**: Use branches to prototype; test thoroughly before merging to `develop` or `main`.
- **Error Handling**: When a command fails, analyze logs, propose fixes, re-execute, and verify.
- **Safety**: Never perform destructive operations; always preserve working code and data.

## Common Tasks

### Adding a New Feature

1. Create a feature branch: `git checkout -b feature/description`.
2. Implement in relevant module (e.g., new extraction logic in `extractor.py`).
3. Write unit tests in `tests/test_extractor.py`.
4. Run linting and tests: `poetry run black . && poetry run pytest --cov=src`.
5. Update docstrings and docs if API changes.
6. Commit atomically: `git commit -m "feat: Add new extraction feature"`.
7. Merge to `develop` after review.

### Debugging a Failing Test

1. Isolate the test: `poetry run pytest tests/test_xyz.py::test_name -v`.
2. Review stack trace and logs.
3. Check if it's environment-related (Ollama running? GPU available?) or code logic.
4. Use `pdb` (Python debugger) or VS Code debugger for step-through.
5. Implement fix, re-run test, verify no regressions.

### Updating Dependencies

1. Check for outdated packages: `poetry show --outdated`.
2. Update specific or all: `poetry update <package>` or `poetry update`.
3. Run full test suite: `poetry run pytest`.
4. Verify no breaking changes in functionality.
5. Commit lock file: `git commit -m "chore: Update dependencies"`.

## External Resources

- **Ollama Models**: https://ollama.ai (Llama 3.2 Vision, DeepSeek-OCR)
- **Marker (Layout Detection Reference)**: https://github.com/datalab-to/marker
- **PDF-Extract-Kit**: https://github.com/opendatalab/PDF-Extract-Kit
- **Poetry Docs**: https://python-poetry.org/docs/
- **pytest Docs**: https://docs.pytest.org/
- **Type Hints (PEP 484)**: https://www.python.org/dev/peps/pep-0484/
- **Google Style Docstrings**: https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings

## Questions or Additions?

If you encounter issues or patterns not covered here, update this file with:
1. The problem or pattern.
2. The solution or convention you've established.
3. Examples if helpful.

Keep this document concise and actionable for future development sessions.
