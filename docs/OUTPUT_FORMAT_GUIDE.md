# OCRSuite Output Format Analysis & Recommendations

## Executive Summary

For production OCR'd documents with formulas, tables, figures, and text, **LaTeX (.tex) is the ideal primary output format** when compiled to PDF, supplemented by **Markdown (.md) for accessibility and web viewing**. This guide explains why and how to implement it in OCRSuite.

## Output Format Comparison

| Format | Text | Formulas | Tables | Figures | Editability | Compilation | Web Ready |
|--------|------|----------|--------|---------|-------------|-------------|-----------|
| **LaTeX (.tex)** | ✅ | ✅✅ | ✅✅ | ✅✅ | ✅ | ✅ PDF/HTML | ⚠️ Needs processing |
| **PDF** | ✅ | ✅ | ✅ | ✅ | ❌ Hard | ❌ Final | ✅ |
| **Markdown (.md)** | ✅ | ⚠️ MathJax | ⚠️ Limited | ⚠️ References | ✅ | ⚠️ Pandoc | ✅ |
| **DOCX** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **HTML** | ✅ | ✅ MathJax | ✅ | ✅ | ✅ | ⚠️ Browser | ✅ |

## Recommended Output Strategy

### Primary Output: LaTeX + PDF
**Why:**
1. **Formulas**: Native support via `amsmath`, `amssymb` packages
   - Inline: `$E=mc^2$`
   - Display: `$$\int_0^\infty e^{-x^2}dx = \frac{\sqrt{\pi}}{2}$$`

2. **Tables**: Professional formatting with `tabular`, `booktabs`
   ```latex
   \begin{tabular}{|l|c|r|}
   \hline
   Column 1 & Column 2 & Column 3 \\
   \hline
   ...
   \end{tabular}
   ```

3. **Figures**: Embedded with `\includegraphics`
   ```latex
   \begin{figure}[h]
   \centering
   \includegraphics[width=0.8\textwidth]{figure_001.png}
   \caption{Figure caption}
   \end{figure}
   ```

4. **Text**: Clean, structured with sections/subsections
5. **Editability**: Source `.tex` can be edited before compilation
6. **Output**: Compile to PDF for final document

### Secondary Output: Markdown
**Why:**
- GitHub/web viewing without processing
- Reference for extraction quality
- Fallback if LaTeX compilation fails

### Tertiary Output: HTML
**Why:**
- Browser viewing without LaTeX installation
- MathJax for formula rendering
- Copy/paste friendly

## Current OCRSuite Output Structure

### Files Generated
```
output/
├── document.tex          # Main LaTeX document
├── extraction.md         # Markdown extraction (reference)
├── metadata.txt          # Processing metadata
└── figure_*.png          # Extracted images
```

### Current Issues
1. **Incomplete extraction** - Pages timeout, [Unrecognized content] placeholder
2. **No formula detection** - Math content not identified/extracted
3. **No table parsing** - Table structure lost
4. **No figure embedding** - Figures extracted but not referenced in LaTeX
5. **No document structure** - Sections/chapters not detected

## Enhanced Output Format Implementation

### Phase 1: Improve LaTeX Output (Immediate)

**Enhance assembler.py to generate:**

```latex
\documentclass[12pt]{book}  % For book-length documents
\usepackage{amsmath, amssymb}  % Math support
\usepackage{graphicx}  % Figure support
\usepackage{booktabs}  % Professional tables
\usepackage{hyperref}  % Cross-references
\usepackage{listings}  % Code blocks
\usepackage{xcolor}  % Colors

% Add to preamble for missing content markers
\newcommand{\unrecognized}[1]{\fbox{[Unrecognized: #1]}}

\begin{document}

\tableofcontents

% Chapter 1: Page groups
\chapter{Chapter 1}
% Page content with proper structure

% Figures
\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{figure_001.png}
\caption{Extracted figure from page 5}
\label{fig:001}
\end{figure}

% Tables
\begin{table}[h]
\centering
\begin{tabular}{|l|c|r|}
\hline
Column 1 & Column 2 & Column 3 \\
\hline
Data 1 & Data 2 & Data 3 \\
\hline
\end{tabular}
\caption{Extracted table}
\label{tbl:001}
\end{table}

% Formulas
Display math: \(E=mc^2\)
Or: \[E=mc^2\]

\end{document}
```

### Phase 2: Add Formula Detection

**Integrate formula recognition:**
```python
def detect_formulas(image):
    """Detect and extract mathematical formulas from image."""
    # Use OCR model with formula-specific prompt:
    prompt = "<image>\n<|grounding|>Extract all mathematical formulas and equations."
    # Return: list of (formula_text, location)

def format_formula(formula_text: str) -> str:
    """Convert detected formula to LaTeX format."""
    # If detected as: "E = mc^2"
    # Return: "$E=mc^2$" or "\\[E=mc^2\\]"
```

### Phase 3: Add Table Structure Parsing

**Enhance table extraction:**
```python
def extract_table_structure(image):
    """Extract table with preserved structure."""
    prompt = "<image>\n<|grounding|>Extract table as markdown with clear column/row alignment."
    # Return: markdown table -> convert to LaTeX tabular

def markdown_table_to_latex(md_table: str) -> str:
    """Convert markdown table to LaTeX tabular environment."""
    # Parse markdown:
    # | Col1 | Col2 |
    # |------|------|
    # | A    | B    |
    # 
    # Generate LaTeX:
    # \begin{tabular}{|l|l|}
    # \hline
    # Col1 & Col2 \\
    # ...
    # \end{tabular}
```

### Phase 4: Add Figure Referencing

**Link extracted figures to LaTeX:**
```python
def create_figure_reference(figure_path: Path, page_num: int, caption: str = "") -> str:
    """Create LaTeX figure reference."""
    return f"""
\\begin{{figure}}[h]
\\centering
\\includegraphics[width=0.8\\textwidth]{{{figure_path.name}}}
\\caption{{{caption or f'Extracted figure from page {page_num}'}}}
\\label{{fig:{page_num:03d}}}
\\end{{figure}}
"""
```

### Phase 5: Multi-Format Output

**Generate all formats:**
```python
def generate_output_formats(content: dict, output_dir: Path):
    """Generate LaTeX, Markdown, HTML, and PDF outputs."""
    
    # 1. Generate LaTeX
    latex_content = assemble_latex(content)
    save_latex("document.tex", latex_content)
    
    # 2. Compile to PDF (optional)
    if has_compiler():
        compile_latex_to_pdf("document.tex")
    
    # 3. Generate Markdown
    markdown_content = assemble_markdown(content)
    save_markdown("extraction.md", markdown_content)
    
    # 4. Generate HTML
    html_content = latex_to_html(latex_content)
    save_html("document.html", html_content)
    
    # 5. Generate summary
    create_summary_report(content, output_dir)
```

## Ideal Output Workflow

```
OCR Processing Pipeline
    ↓
Extract: Text, Formulas, Tables, Figures
    ↓
Organize: Group by page/section/chapter
    ↓
Generate:
    ├─→ document.tex (editable source)
    ├─→ document.pdf (final output)
    ├─→ extraction.md (web-friendly)
    ├─→ document.html (browser viewable)
    ├─→ README.md (processing report)
    └─→ figure_*.png (extracted images)
    ↓
Compile: LaTeX → PDF (optional, if compiler available)
    ↓
Final Output: PDF (primary) + HTML (web) + LaTeX source (editable)
```

## Implementation Priority

### Tier 1 (Essential)
- [ ] Fix timeout issues (DONE via Modelfile)
- [ ] Enhance LaTeX preamble with packages
- [ ] Add table of contents support
- [ ] Link figures in LaTeX output

### Tier 2 (High Value)
- [ ] Formula detection and extraction
- [ ] Table structure parsing
- [ ] Multi-format output (LaTeX, Markdown, HTML)
- [ ] PDF compilation

### Tier 3 (Nice to Have)
- [ ] Section/chapter auto-detection
- [ ] Cross-references and bookmarks
- [ ] Index generation
- [ ] Bibliography support

## File Structure Recommendation

```
output/
├── document.tex              # Main LaTeX source (editable)
├── document.pdf              # Compiled PDF (final)
├── document.html             # HTML version (web)
├── extraction.md             # Markdown reference
├── figures/
│   ├── figure_001.png       # Extracted figures
│   ├── figure_002.png
│   └── ...
├── tables/
│   ├── table_001.txt        # Extracted tables (markdown)
│   └── ...
├── formulas.txt             # Extracted formulas (reference)
├── metadata.json            # Processing metadata
└── README.md                # Generation report
```

## LaTeX Preamble Enhancements

**Current:**
```latex
\documentclass[12pt]{article}
\usepackage{amsmath, amssymb, graphicx}
```

**Recommended:**
```latex
\documentclass[12pt]{book}
\usepackage[utf-8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath, amssymb, mathtools}  % Math
\usepackage{graphicx, float}               % Figures
\usepackage{booktabs, longtable}           % Tables
\usepackage{hyperref}                       % Links/bookmarks
\usepackage{xcolor, listings}              % Code highlighting
\usepackage{geometry}                       % Page margins
\usepackage{fancyhdr}                       % Headers/footers
\usepackage{tocbibind}                      % TOC formatting

% Color definitions
\definecolor{codebackground}{gray}{0.95}
\definecolor{codefont}{rgb}{0.2,0.2,0.2}

% Hyperref settings
\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=blue,
    urlcolor=blue,
    bookmarksopen=true
}

% Code listing style
\lstset{
    backgroundcolor=\color{codebackground},
    basicstyle=\ttfamily\small,
    breaklines=true,
    tabsize=2
}

% Custom commands
\newcommand{\unrecognized}[1]{\textit{[Unrecognized: #1]}}
```

## Prompts for Enhanced OCR

### For Formula Extraction
```
"<image>\n<|grounding|>Extract ALL mathematical formulas and equations. 
For each formula found, provide:
1. The formula text/notation
2. Its location (top/middle/bottom)
3. Whether it's inline or display"
```

### For Table Extraction
```
"<image>\n<|grounding|>Extract the table structure as markdown with proper 
column and row alignment. Preserve the column headers and data relationships."
```

### For Figure Analysis
```
"<image>\n<|grounding|>Identify all figures, charts, diagrams, and graphs. 
For each, provide a descriptive caption and indicate what type it is."
```

### For Document Structure
```
"<image>\n<|grounding|>Identify the document structure: 
- Chapter/section titles
- Subsections
- Any special formatting (bold, italic, headers)
- Page numbers and headers/footers"
```

## Implementation Roadmap

**Short Term (This week):**
1. Enhance LaTeX preamble with more packages
2. Add figure linking in LaTeX output
3. Create comprehensive output documentation
4. Test with actual books

**Medium Term (Next 2 weeks):**
1. Implement formula detection
2. Implement table parsing
3. Add HTML export
4. Create output format guide

**Long Term (Month 1):**
1. Auto-detect document structure
2. Generate comprehensive table of contents
3. Add cross-references
4. Support for special document types (textbooks, research papers, etc.)

## Conclusion

**LaTeX → PDF** is the ideal primary output because it:
- Natively supports formulas, tables, and figures
- Provides professional formatting
- Is editable before final compilation
- Can compile to PDF (final form) or HTML (web viewing)
- Is the standard in academic/scientific publishing

**Markdown** should be a secondary output for accessibility and web viewing.

The current OCRSuite implementation generates LaTeX, but needs enhancement to:
1. Properly detect and format formulas
2. Parse and structure tables
3. Link extracted figures
4. Support multi-format output
5. Increase context window and timeout for complex documents (DONE via Modelfile)

See `MODELFILE.md` and `LATEX_VERIFICATION.md` for current LaTeX/PDF support. Next steps are implementing formula and table detection.
