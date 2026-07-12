# AI-Based PDF Processing App Specification

## 1. Overview

### 1.1 Purpose

This app is an AI-powered tool for digitizing old books from PDF inputs. It leverages free, open-source (OSS), and locally hostable models—focusing on Ollama-hosted vision models for OCR and processing—to extract and separate content. The system identifies text (including inline math formulas), tables, and figures, then outputs:

- A single LaTeX document containing the extracted text and math formulas.
- Individual PNG files for extracted figures.
- A Markdown file for converted tables.

The app emphasizes local execution for privacy and control, avoiding cloud dependencies. It's optimized for scanned or born-digital PDFs of old books, which may include degraded text, complex layouts, mathematical notations, and illustrations.

### 1.2 Key Features

- **Input Handling**: Accepts a single PDF file (scanned or vector-based).
- **Content Separation**: Uses layout analysis to distinguish text/math, tables, and figures.
- **OCR and Recognition**: Employs multimodal models for accurate extraction, especially for math and degraded text.
- **Output Formats**:
  - LaTeX (.tex) for narrative text and inline/block math.
  - PNG images for figures (e.g., diagrams, illustrations).
  - Markdown (.md) for tables, preserving structure.
- **Local Hosting**: All models run via Ollama or compatible OSS frameworks.
- **Error Handling**: Graceful degradation for low-quality scans, with logging.
- **Extensibility**: Modular design for swapping models or adding pre/post-processing.

### 1.3 Assumptions and Constraints

- PDFs are primarily text-based books; not optimized for heavily image-only or non-English content (though multilingual support is included).
- Hardware: Requires a machine with GPU for efficient Ollama model inference (e.g., NVIDIA with CUDA).
- No internet access needed post-setup; all tools are local.
- Free/OSS only: No proprietary APIs like Mathpix.

## 2. System Architecture

The app follows a pipeline architecture, processing the PDF in stages. High-level flow:

1. **PDF Preprocessing**: Convert PDF to images or parse vector elements.
2. **OCR and Extraction**: Send images to Ollama vision models for text/math/table/figure extraction.
3. **Assembly and Output**: Compile extracted content into files.
4. **Post-Processing (optional)**: Llava vision model enriches Markdown (tables, links, lists) and converts figures to ASCII art via Canny edge detection.

### 2.1 Components and Tools

We select the best free/OSS tools based on benchmarks for accuracy in handling old books (degraded text, math, tables, figures). Priority given to Ollama-compatible models for AI integration.

#### 2.1.1 PDF Parsing and Image Conversion

- **Tool**: pdf2image (Python library, OSS).
- **Role**: Convert PDF pages to high-resolution images (e.g., 300 DPI) for OCR. For born-digital PDFs, optionally use PyMuPDF for vector extraction to improve accuracy.
- **Why?**: Handles scanned PDFs common in old books; simple, local.

#### 2.1.2 Layout Detection

- **Tool**: Surya (from Datalab, OSS, integrated in Marker).
- **Role**: Analyze page images to detect bounding boxes for text blocks, math regions, tables, and figures. Supports 90+ languages, complex layouts.
- **Alternative**: PDF-Extract-Kit (OSS) for integrated layout, formula, and table detection.
- **Why?**: Excels at structural understanding in documents with math/tables; local execution.

#### 2.1.3 OCR and Content Recognition

- **Primary Models (Ollama-Hosted)**:
  - **Llama 3.2 Vision (11B or 90B)**: Multimodal LLM for high-accuracy OCR on complex docs, including handwriting and degraded text. Handles text, math, and structure preservation.
  - **DeepSeek-OCR**: Token-efficient for OCR on text, charts, formulas. Unifies parsing in a single pass.
  - **Granite3.2-Vision**: Compact for visual doc understanding, extracting from tables/charts/infographics.
- **Fallback/Supplementary**:
  - **PaddleOCR (OSS)**: For table recognition and multilingual text; integrates well with layouts.
  - **Tesseract OCR (OSS)**: Base text extraction; trainable for old fonts.
- **Role**: Process detected regions:
  - Text/Math: Convert to LaTeX (e.g., prompt Llama 3.2: "Extract text and convert math to LaTeX.").
  - Tables: Recognize structure and output Markdown.
- **Why Ollama?**: Local hosting of vision LLMs; supports prompts for custom separation (e.g., "Separate inline math from text"). Benchmarks show Llama 3.2 outperforming on noisy scans.

#### 2.1.4 Math Formula Extraction

- **Tool**: Integrated with OCR models above; supplement with LaTeX-OCR (OSS) for isolated formulas.
- **Role**: Detect inline/block math, convert to LaTeX markup (e.g., \( ... \) or $$ ... $$).
- **Alternative**: Nougat (OSS) for end-to-end academic PDF to LaTeX/MD with math.
- **Why?**: Ollama models like DeepSeek-OCR handle formulas natively; high accuracy for old books' notations.

#### 2.1.5 Table Conversion

- **Tool**: PaddleOCR + TableMaster (from PDF-Extract-Kit) or StructEqTable.
- **Role**: Detect table images, recognize cells/rows, output as Markdown tables (e.g., | Col1 | Col2 |).
- **Integration**: Use Ollama prompts for refinement (e.g., "Convert this table image to Markdown.").
- **Why?**: Handles complex tables with math; OSS and local.

#### 2.1.6 Figure Extraction

- **Tool**: OpenCV (OSS) for cropping based on layout boxes.
- **Role**: Isolate figures from page images, save as individual PNGs (e.g., figure_1.png).
- **Why?**: Simple, efficient; preserves original quality.

#### 2.1.7 Post-Processing and Assembly

- **Tools**: Python scripts, pylatex for LaTeX generation, OpenCV for Canny edge detection.
- **Role**:
  - Compile text/math into Markdown and LaTeX output.
  - Log errors (e.g., unrecognized regions).
  - Optional: Llava vision model enriches Markdown (tables, links, lists) and converts figures to ASCII art.

#### 2.1.8 Figure Post-Processing (Canny + Llava)

- **Tool**: OpenCV (Canny edge detection) + Llava vision model.
- **Role**: Convert extracted figures to ASCII art for lossless, readable output.
  1. Load figure as grayscale.
  2. Apply Canny edge detection (low=50, high=150) to extract structural edges.
  3. Send edge image to Llava with prompt: "Describe this as ASCII art using box-drawing characters."
  4. Output as fenced Markdown code block.
- **Why?**: Canny reduces noise from degraded paper and highlights structural lines. Llava's general vision handles diverse figure types (diagrams, charts, illustrations).

### 2.2 Data Flow

| Stage           | Input          | Process                       | Output                                        |
| --------------- | -------------- | ----------------------------- | --------------------------------------------- |
| Preprocessing   | PDF file       | Convert to page images/vector | List of images/regions                        |
| Layout Analysis | Page images    | Detect bounding boxes         | JSON with regions (text, math, table, figure) |
| OCR/Extraction  | Regions        | Apply Ollama models           | Raw text/LaTeX/math, table MD, figure crops   |
| Assembly        | Extracted data | Compile                       | extraction.md, figures/*.png                  |
| Post-processing | extraction.md, figures | Llava vision model    | postprocessed.md (tables, links, ASCII art)   |

## 3. Implementation Details

### 3.1 Technology Stack

- **Language**: Python 3.12+ (for compatibility with tools).
- **Dependencies** (all OSS):
  - Ollama: For hosting/running vision models.
  - pdfplumber: PDF page rendering (replaced pdf2image for Windows-native compatibility).
  - OpenCV: Canny edge detection for figure post-processing.
  - loguru: ISO 8601 structured logging with rotation and retention.
  - NiceGUI: Desktop + web GUI with async pipeline execution.
  - Typer + Rich: CLI with progress bars.
- **Setup Script**: Automate model pulls (e.g., `ollama pull llama3.2-vision`).

### 3.2 User Interface

- **CLI First**: Command-line app (e.g., `python app.py --input book.pdf --output dir/`).
- **Optional GUI**: Use Streamlit (OSS) for file upload/preview.
- **Config File**: YAML for model selection (e.g., primary_ocr: llama3.2-vision).

### 3.3 Performance Considerations

- **Batch Processing**: Process pages in parallel (multiprocessing).
- **Resource Management**: Limit Ollama to available GPU VRAM (e.g., 11B model for efficiency).
- **Accuracy Tuning**: Prompts for Ollama (e.g., "Focus on old book text with math: extract precisely.").
- **Testing**: Benchmark on datasets like old math books (e.g., from arXiv or Project Gutenberg).

### 3.4 Error Handling and Logging

- Handle degraded scans: Fallback to Tesseract if LLM hallucinates.
- Log: Verbose output for unrecognized elements.
- Validation: Post-check LaTeX compilation.

## 4. Development Roadmap

1. **Prototype**: Integrate PDF to images + OCR.
2. **Core Features**: Math, table, figure extraction.
3. **Optimization**: Tune prompts for DeepSeek-OCR command DSL.
4. **Testing**: 41 tests, 57% coverage on sample book PDFs.
5. **GUI**: Desktop + web interface (NiceGUI) with live progress and bottleneck tracking.
6. **Post-Processing**: Canny edge detection + Llava for ASCII art and Markdown enrichment.

## 5. References and Resources

- Ollama Models: Llama 3.2 Vision, DeepSeek-OCR (ollama.com).
- Tools: Marker (github.com/datalab-to/marker), PDF-Extract-Kit (github.com/opendatalab/PDF-Extract-Kit), PaddleOCR (github.com/PaddlePaddle/PaddleOCR).
- Benchmarks: From sources like Modal.com's OCR comparison, emphasizing math/table handling.

## 6. Development Guidelines and Best Practices

This chapter outlines how to implement the app as a professional, open-source Python project. It emphasizes elegant code, Windows-specific building, best tools, a structured development process, and a standard project tree. We adhere to PEP standards (e.g., PEP 8 for style, PEP 621 for packaging), community best practices from projects like FastAPI or Scikit-learn, and principles of clean architecture for maintainability.

### 6.1 Writing Elegant and Applicable Python Code

To ensure the code is readable, maintainable, and efficient—hallmarks of professional OSS projects—follow these guidelines:

- **Style and Formatting**: Adhere to PEP 8. Use Black for auto-formatting (line length 88) and isort for imports. Avoid dense code; favor clarity over cleverness.
- **Modularity**: Break the pipeline into classes/modules (e.g., `pdf_preprocessor.py`, `layout_analyzer.py`). Use dependency injection for swappable components (e.g., via dataclasses or protocols).
- **Type Hints**: Use typing (PEP 484) for all functions/classes. Employ mypy for static checking.
- **Error Handling**: Use structured exceptions (custom subclasses of Exception) and loguru for structured logging (ISO 8601 timestamps, rotation, retention).
- **Performance**: Profile with cProfile; optimize hotspots (e.g., parallelize page processing with concurrent.futures). Use context managers for resources (e.g., with open()).
- **Documentation**: Inline docstrings (Google or NumPy style) for every function/class. Generate docs with Sphinx.
- **Testing**: Aim for 80%+ coverage with pytest. Include unit tests (e.g., for layout detection), integration tests (full pipeline on sample PDFs), and edge cases (degraded scans).
- **Best Practices Examples**:
  - Prefer list comprehensions over loops for conciseness.
  - Use f-strings for formatting.
  - Avoid global state; pass configs explicitly.
  - For Ollama integration: Wrap API calls in a service class for easy mocking in tests.

Code should feel "Pythonic": simple, explicit, and error-resistant, as per the Zen of Python (import this).

### 6.2 Best Tools for Building

Select tools that enhance productivity, quality, and collaboration, aligned with OSS standards:

- **IDE/Editor**: Visual Studio Code (VS Code) with extensions: Python, Pylance, Black Formatter, Jupyter (for prototyping prompts).
- **Dependency Management**: Poetry (superior to pip for lockfiles and virtualenvs). Use pyproject.toml for metadata (PEP 621).
- **Version Control**: Git with GitHub for hosting. Follow Git Flow: main for releases, develop for integration, feature branches.
- **Formatting/Linting**: Black, isort, flake8, mypy. Integrate via pre-commit hooks.
- **Testing**: pytest with pytest-cov for coverage. Hypothesis for property-based testing on edge cases.
- **Documentation**: Sphinx with ReadTheDocs theme; auto-generate from docstrings.
- **CI/CD**: GitHub Actions for linting, testing, and building on push/PR. Include Windows runners.
- **Profiling/Debugging**: cProfile, pdb (or VS Code debugger). Memory profiling with memory_profiler.
- **Containerization**: Docker for reproducible environments (e.g., bundle Ollama and deps).
- **Windows-Specific**: Use WSL2 (Windows Subsystem for Linux) for Linux-like dev if needed, but build natively. Install via winget (e.g., winget install --id Git.Git).

These tools ensure a robust workflow, as seen in projects like Hugging Face Transformers.

### 6.3 Development Process on Windows

Build iteratively on Windows 10/11, focusing on cross-platform compatibility (test on Linux/Mac via CI). Process:

1. **Setup Environment**:
   - Install Python 3.12 via official installer (enable "Add to PATH").
   - Install Poetry: `(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -`.
   - Install Git: winget install --id Git.Git.
   - Install Ollama: Download from ollama.com; run `ollama serve` in a separate terminal.
    - Create project: `uv init ocrsuite`; cd into it.
   - Add deps: `poetry add pdf2image pymupdf opencv-python paddleocr tesseract-ocr pylatex` (etc.). For Ollama, use ollama-python lib.
   - Handle Windows quirks: Use os.path for paths; install Visual C++ Build Tools for native deps (e.g., OpenCV).

2. **Prototype Phase**:
   - Scaffold structure (see 6.4).
   - Implement core pipeline in Jupyter notebooks for rapid iteration (e.g., test Ollama prompts).
   - Commit early: git init, add .gitignore (python template).

3. **Implementation Phase**:
   - Develop feature by feature (e.g., PDF to images first).
   - Run locally: `poetry run python src/main.py`.
   - Debug: Use VS Code's debugger; handle GPU setup (install CUDA via NVIDIA toolkit if using GPU Ollama).

4. **Testing and Optimization**:
   - Write tests in tests/ dir.
   - Lint: `poetry run black .`; `poetry run mypy .`.
   - Profile: Run on sample PDFs; optimize for Windows perf (e.g., avoid fork in multiprocessing, use ThreadPool).

5. **Documentation and Packaging**:
   - Build docs: `poetry run sphinx-build docs build/html`.
   - Package: Add entry_points in pyproject.toml for CLI (e.g., console_scripts).
   - Release: Tag versions (semantic versioning); publish to PyPI if OSS.

6. **Deployment**:
   - Build Docker image: Use multi-stage Dockerfile for Windows compatibility.
   - Test end-to-end: Process a full book PDF.

Emphasize small commits, PR reviews (even solo via branches), and weekly iterations. Total timeline: 2-4 weeks for MVP.

### 6.4 Project Tree Structure

Follow Cookiecutter or standard OSS layout (e.g., from PyPA) for professionalism:

```
ocrsuite/
├── .github/                # CI workflows
│   └── workflows/          # GitHub Actions YAML
├── docs/                   # Sphinx source
│   ├── conf.py
│   └── index.rst
├── src/                    # Main code (package)
│   ├── pdf_processor_app/
│   │   ├── __init__.py
│   │   ├── main.py         # Entry point/CLI
│   │   ├── config.py       # YAML config loader
│   │   ├── preprocessor.py # PDF to images
│   │   ├── analyzer.py     # Layout detection
│   │   ├── ocr_engine.py   # Ollama/Paddle integration
│   │   ├── extractor.py    # Math/table/figure
│   │   └── assembler.py    # Output compilation
│   └── setup.py            # If needed for legacy
├── tests/                  # Pytest tests
│   ├── __init__.py
│   ├── test_preprocessor.py
│   └── resources/          # Sample PDFs for tests
├── .gitignore
├── LICENSE                 # MIT or Apache 2.0
├── README.md               # Project overview, install guide
├── pyproject.toml          # Poetry config, deps, metadata
├── poetry.lock             # Locked deps
└── Dockerfile              # For containerization
```

This structure promotes separation of concerns, easy testing, and scalability—ready for contributions.
