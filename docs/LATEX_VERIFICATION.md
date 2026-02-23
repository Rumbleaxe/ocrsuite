# LaTeX Verification & PDF Compilation

OCRSuite includes built-in LaTeX verification to ensure the generated `.tex` files are valid before attempting to compile them to PDF.

## Features

### ✅ Automatic LaTeX Validation
When OCRSuite saves a LaTeX document, it automatically validates:
- Document structure (required `\documentclass`, `\begin{document}`, `\end{document}`)
- Matching braces `{}` and brackets `[]`
- Valid LaTeX syntax

### 📄 Optional PDF Compilation
If you have a LaTeX compiler installed, OCRSuite can compile the generated `.tex` files to PDF for verification.

## Installation

### Compiler Options

Choose one of the following:

#### Option 1: Tectonic (Recommended) ⭐
Modern, self-contained, no external dependencies.

```powershell
# Using Chocolatey
choco install tectonic

# Or using Cargo (Rust)
cargo install tectonic

# Or download from GitHub
# https://github.com/tectonic-typesetting/tectonic/releases
```

#### Option 2: MiKTeX (Windows-Native)
Traditional TeX distribution for Windows.

```powershell
# Using Chocolatey
choco install miktex

# Or download from
# https://miktex.org/download
```

#### Option 3: TeX Live
Comprehensive TeX installation.

```powershell
# Using Chocolatey
choco install texlive

# Or use the installer from
# https://www.tug.org/texlive/
```

## Usage

### Automatic Verification

LaTeX files are automatically verified when generated:

```powershell
ocrsuite process --input book.pdf --output ./output/

# Output will show:
# [cyan]Extracting content with Ollama...[/cyan]
# LaTeX document generated
# LaTeX syntax validated successfully
```

### Check Verification Status

```powershell
python -c "from ocrsuite.latex_verifier import LaTeXVerifier; v = LaTeXVerifier(); print(v.get_status())"
```

**Output example:**
```
LaTeX Verification Status:
  ✓ Tectonic (recommended)
  ✓ pdflatex
```

### Compile to PDF

If a compiler is installed, compile the generated LaTeX:

```powershell
# Using Tectonic
tectonic document.tex

# Or using pdflatex
pdflatex document.tex

# Or using latexmk (if installed)
latexmk -pdf document.tex
```

## Programmatic Usage

### Python API

```python
from ocrsuite.latex_verifier import LaTeXVerifier
from pathlib import Path

# Initialize verifier
verifier = LaTeXVerifier()

# Validate a LaTeX file
tex_file = Path("document.tex")
is_valid, errors = verifier.validate_latex_syntax(tex_file)

if is_valid:
    print("✓ LaTeX is valid")
else:
    print(f"✗ Errors found: {errors}")

# Compile to PDF (if compiler available)
success, message = verifier.compile_to_pdf(tex_file)
print(message)

# Check what's available
print(verifier.get_status())
```

## Troubleshooting

### LaTeX Validation Issues

**Problem:** LaTeX validation reports errors

**Solutions:**
1. Check for unmatched braces: `{text` missing `}`
2. Check for unmatched brackets: `[text` missing `]`
3. Ensure `\documentclass` is at the start
4. Ensure `\begin{document}` and `\end{document}` are present

### PDF Compilation Failed

**Problem:** `tectonic` or `pdflatex` not found

**Solutions:**
1. Install one of the recommended compilers above
2. Ensure the compiler is in your PATH
3. Try a different compiler (Tectonic is most reliable)

```powershell
# Verify compiler is installed
tectonic --version
pdflatex --version
```

### "No LaTeX compiler found"

**Problem:** OCRSuite can validate syntax but can't compile to PDF

**Solution:**
Install Tectonic or pdflatex (see Installation section above)

## Best Practices

1. **Always verify output** – Check `extraction.md` or `document.tex` for quality
2. **Use Tectonic for CI/CD** – It's self-contained and doesn't require system TeX
3. **Check validation warnings** – Warnings are logged but don't stop processing
4. **Manual inspection** – Open the generated PDF in a reader to verify quality

## Advanced Configuration

### Custom LaTeX Compilation

For advanced users, you can manually compile with custom options:

```powershell
# With interaction disabled
pdflatex -interaction=nonstopmode document.tex

# With multiple passes for cross-references
latexmk -pdf -interaction=nonstopmode document.tex
```

### Tectonic with Fontawesome

```powershell
# Enable fontawesome icons in LaTeX
tectonic --bundle full document.tex
```

## See Also

- [OCRSuite README](README.md)
- [QUICKSTART Guide](QUICKSTART.md)
- [Tectonic Documentation](https://tectonic-typesetting.github.io/)
- [MiKTeX Documentation](https://docs.miktex.org/)
