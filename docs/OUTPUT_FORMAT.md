# OCRSuite Output Format

## Overview

OCRSuite now generates **a single consolidated Markdown file** containing all extracted content with linked figures, making it easier to manage, view, and distribute the output.

## Output Structure

### Single Markdown File

The main output is a Markdown file with the naming format:

```
DDMMYY_HHMMSS_ORIGINNAME.md
```

**Examples:**
- `230226_185410_book.md` - Created Feb 23, 2026 at 18:54:10 from book.pdf
- `250101_120000_myeBook.md` - Created Jan 1, 2025 at 12:00:00 from myeBook.pdf

### Figures Directory (Optional)

If your document contains figures/illustrations, they are extracted to a companion directory:

```
DDMMYY_HHMMSS_ORIGINNAME/
├── figure_001.png
├── figure_002.png
└── figure_003.png
```

The figures directory is only created if figures are detected and extracted.

### Log File

A detailed processing log is always generated:

```
log.txt
```

Contains timestamps, debug information, and any errors encountered during processing.

## Markdown File Format

### Structure

```markdown
# Original Document Title

*Generated: 2026-02-23 18:54:10*

## page_0001 (content_type)

[Page content - text, tables, or figure references]

## page_0002 (content_type)

[Page content]

---

## Processing Notes

- Pages processed: 42
- Errors: 0
  - (List of any processing errors)
```

### Content Types

Each page header includes the detected content type:

- **text** - Plain text content
- **table** - Structured table data
- **figure** - Diagrams, charts, illustrations
- **mixed** - Multiple content types on one page
- **unknown** - Could not be classified

### Figure References

When figures are detected, they are embedded as Markdown links:

```markdown
![Figure 1](230226_185410_book/figure_001.png)
```

This allows viewers to see figures inline when the Markdown is rendered, and the link works as long as the figures directory exists alongside the markdown file.

## Directory Layout Example

After processing a PDF named `book.pdf`:

```
output/
├── 230226_185410_book.md          # Main output file
├── 230226_185410_book/            # Figures directory (if figures found)
│   ├── figure_001.png
│   ├── figure_002.png
│   └── figure_003.png
└── log.txt                        # Processing log
```

## Usage

The single Markdown file can be:

1. **Viewed directly** - Open in any Markdown viewer
2. **Converted** - Use tools like Pandoc to convert to other formats
   ```bash
   pandoc 230226_185410_book.md -o book.docx
   pandoc 230226_185410_book.md -o book.pdf
   ```
3. **Distributed** - Share with others; recipients only need the .md file + figures folder
4. **Edited** - Edit in any text editor to refine content
5. **Version controlled** - Commit to git, as .md files are text-based

## Processing Notes

The footer section contains:

- **Pages processed** - Number of pages successfully extracted
- **Errors** - Any processing errors encountered (timeouts, failures)

This provides transparency about the extraction quality and whether all pages were successfully processed.

## Advantages of This Format

✅ **Single file** - Easier to manage and distribute  
✅ **Portable** - Markdown + figures folder is all you need  
✅ **Readable** - Clean, human-readable format  
✅ **Linkable** - Figures automatically embedded and linked  
✅ **Editable** - Edit in any text editor  
✅ **Convertible** - Use Pandoc/Markdown tools for other formats  
✅ **Version control friendly** - Works well with git  
✅ **Timestamped** - Filename includes creation time for easy sorting  

## Differences from Previous Format

Previously, OCRSuite generated 3-4 separate files:
- `document.tex` (LaTeX format)
- `extraction.md` (Markdown)
- `metadata.txt` (Metadata)
- `figure_*.png` (Scattered figures)

Now it generates:
- `DDMMYY_HHMMSS_NAME.md` (Single unified output)
- `DDMMYY_HHMMSS_NAME/` (Organized figures folder, if needed)
- `log.txt` (Processing log)

This simplification makes the output more manageable and user-friendly.
