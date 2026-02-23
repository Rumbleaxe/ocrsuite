# OCRSuite Logging Guide

OCRSuite includes a comprehensive logging system that captures detailed processing information in `/output/log.txt` while maintaining concise console output.

## Overview

The logging system provides:
- **Concise console output** - Essential information only, clean and readable
- **Detailed file logging** - Complete processing timeline with debug information
- **Automatic rotation support** - Logs don't grow unbounded
- **Structured logging** - Timestamps, log levels, module names for easy analysis

## Log File Location

```
output/
└── log.txt         # Main logging file (created during processing)
```

## Logging Levels

| Level | Meaning | Examples |
|-------|---------|----------|
| **DEBUG** | Detailed diagnostic information | Variable values, function calls |
| **INFO** | General informational messages | Processing milestones, configuration |
| **WARNING** | Warning messages (problems that don't stop processing) | Skipped content, recoverable errors |
| **ERROR** | Error messages (failures in processing) | Failed to process page, timeout |
| **CRITICAL** | Critical errors (processing cannot continue) | Cannot connect to Ollama |

## Log Output Format

### Console (Concise)
```
INFO | Loading configuration...
INFO | Configuration loaded
INFO | Checking Ollama connection...
INFO | Processing complete!
```

### File (Detailed)
```
2026-02-23 14:15:30 | ocrsuite              | INFO     | Loading configuration...
2026-02-23 14:15:30 | ocrsuite              | INFO     | Configuration loaded: model=ocrsuite-deepseek
2026-02-23 14:15:31 | ocrsuite              | WARNING  | Page 0001: Timeout after 120s
2026-02-23 14:15:32 | ocrsuite.ollama_client| DEBUG    | Sending request to http://localhost:11434
```

## Usage

### Enable Logging

Logging is automatically enabled when you run OCRSuite:

```bash
# Standard logging (INFO level to console, DEBUG to file)
ocrsuite process --input book.pdf --output ./output/

# Verbose logging (DEBUG level to both console and file)
ocrsuite process --input book.pdf --output ./output/ --verbose
```

### Access Log File

After processing, view the log:

```bash
# Windows PowerShell
cat ./output/log.txt

# Linux/Mac
cat ./output/log.txt

# View last 50 lines
tail -50 ./output/log.txt

# Search for errors
grep "ERROR\|CRITICAL" ./output/log.txt
```

## Log Structure

### Processing Timeline Example

```
2026-02-23 14:15:30 | ocrsuite              | INFO     | ================================================================================
2026-02-23 14:15:30 | ocrsuite              | INFO     | OCRSuite Logging Started - 2026-02-23T14:15:30.123456
2026-02-23 14:15:30 | ocrsuite              | INFO     | Log Level: INFO
2026-02-23 14:15:30 | ocrsuite              | INFO     | Log File: C:\project\output\log.txt
2026-02-23 14:15:30 | ocrsuite              | INFO     | ================================================================================
2026-02-23 14:15:30 | ocrsuite              | INFO     | Processing PDF: C:\project\book.pdf
2026-02-23 14:15:30 | ocrsuite              | INFO     | Output directory: C:\project\output

2026-02-23 14:15:31 | ocrsuite              | INFO     | Configuration loaded from: config.yaml
2026-02-23 14:15:31 | ocrsuite              | INFO     | Configuration ready: model=ocrsuite-deepseek, dpi=300, timeout=300s
2026-02-23 14:15:31 | ocrsuite              | INFO     | Connecting to Ollama at http://localhost:11434...
2026-02-23 14:15:31 | ocrsuite              | INFO     | ✓ Connected to Ollama at http://localhost:11434

2026-02-23 14:15:32 | ocrsuite              | INFO     | Reading PDF: book.pdf
2026-02-23 14:15:32 | ocrsuite              | INFO     | PDF info: 40 pages

2026-02-23 14:15:33 | ocrsuite.preprocessor | INFO     | Converting page 0001: book.pdf → page_0001.png
2026-02-23 14:15:34 | ocrsuite.preprocessor | INFO     | Converted 40 pages to images

2026-02-23 14:16:00 | ocrsuite.ollama_client| DEBUG    | Sending request to http://localhost:11434/api/generate
2026-02-23 14:16:05 | ocrsuite              | INFO     | ✓ Extraction complete: 38 pages processed, 2 errors

2026-02-23 14:16:05 | ocrsuite              | INFO     | Assembling output files...
2026-02-23 14:16:05 | ocrsuite              | INFO     | ✓ LaTeX document saved: document.tex
2026-02-23 14:16:05 | ocrsuite              | INFO     | ✓ Markdown file saved: extraction.md
2026-02-23 14:16:05 | ocrsuite              | INFO     | ✓ Metadata file saved: metadata.txt

2026-02-23 14:16:05 | ocrsuite              | INFO     | OCRSuite processing completed successfully!
2026-02-23 14:16:05 | ocrsuite              | INFO     | OCRSuite process finished. Log file: C:\project\output\log.txt
```

## Key Logged Information

### Configuration Phase
```
Configuration loaded: model=ocrsuite-deepseek
Configuration: dpi=300, timeout=300s, max_pages=None
```

### Connection Phase
```
Connecting to Ollama at http://localhost:11434...
✓ Connected to Ollama (model: ocrsuite-deepseek)
```

### Processing Phase
```
Reading PDF: book.pdf
PDF info: 40 pages

Processing page 0001/0040...
Processing page 0002/0040...
[...]

✓ Extraction complete: 38 pages processed, 2 errors
  - page_0001: Timeout after 300s
  - page_0002: Connection refused
```

### Output Phase
```
✓ LaTeX document saved: document.tex
✓ Markdown file saved: extraction.md
✓ Metadata file saved: metadata.txt
```

## Error Logging

Errors are logged with full context:

```
2026-02-23 14:16:20 | ocrsuite              | ERROR    | Error processing page_0005.png: Timeout after 300s
2026-02-23 14:16:20 | ocrsuite              | DEBUG    | Traceback (most recent call last):
  File "ocrsuite/main.py", line 170, in process
    text = client.ocr_image(image_path)
  ...
  TimeoutError: Request timed out
```

## Debugging Tips

### Find Processing Errors
```bash
# Linux/Mac
grep "ERROR\|CRITICAL" ./output/log.txt

# Windows PowerShell
Select-String "ERROR|CRITICAL" ./output/log.txt
```

### Check Processing Speed
```bash
# View timing information
grep "Processing\|complete" ./output/log.txt

# Measure processing time (Linux/Mac)
grep "^2026" ./output/log.txt | head -1
grep "^2026" ./output/log.txt | tail -1
```

### Review Configuration
```bash
# Check what configuration was used
grep "Configuration\|model\|dpi\|timeout" ./output/log.txt | head -20
```

### Trace Ollama Issues
```bash
# Check Ollama connection attempts
grep "Ollama\|localhost:11434" ./output/log.txt
```

## Log Format Specification

### Console Format
```
{LEVEL} | {MESSAGE}
```

Example:
```
INFO | Processing PDF: book.pdf
ERROR | Could not connect to Ollama
```

### File Format
```
{TIMESTAMP} | {LOGGER_NAME:<20} | {LEVEL:<8} | {MESSAGE}
```

Example:
```
2026-02-23 14:15:30 | ocrsuite.preprocessing| INFO     | Converting PDF to images...
```

### Timestamp Format
```
YYYY-MM-DD HH:MM:SS
```

## Performance Impact

- **Console logging** - Minimal overhead (only essential messages)
- **File logging** - Small overhead (~2-3% additional processing time)
- **Log file size** - Typically 5-50 KB per run depending on verbosity

## Disabling Specific Loggers

For development/debugging, you can suppress specific module logging:

```python
import logging

# Suppress debug messages from preprocessor
logging.getLogger("ocrsuite.preprocessor").setLevel(logging.INFO)
```

## Integration with Other Tools

### Send logs to file without running OCRSuite
```bash
# Not applicable - logs are only generated during processing
```

### Append to existing log
```bash
# Each run creates a new log file (no append)
# Store previous logs manually if needed
```

### Parse logs programmatically
```python
import re
from pathlib import Path

log_file = Path("output/log.txt")
with open(log_file) as f:
    for line in f:
        if "ERROR" in line:
            print(f"Error found: {line}")
```

## Best Practices

1. **Always check the log for errors** - If processing seems incomplete, check for ERROR/CRITICAL messages
2. **Keep logs for debugging** - Archive logs with their output for future reference
3. **Use verbose mode for debugging** - Use `--verbose` flag when investigating issues
4. **Check log size** - Logs are automatically created fresh each run
5. **Include logs in bug reports** - When reporting issues, include the log.txt file

## Future Enhancements

Potential logging improvements for future releases:
- [ ] Log rotation (keep last N logs)
- [ ] JSON logging format for programmatic analysis
- [ ] Performance metrics (processing speed, memory usage)
- [ ] Machine-readable error codes
- [ ] Remote logging (send logs to server)
- [ ] Real-time log streaming

## See Also

- [QUICKSTART.md](../QUICKSTART.md) - Getting started
- [README.md](../README.md) - Feature overview
- [MODELFILE.md](MODELFILE.md) - Model configuration
