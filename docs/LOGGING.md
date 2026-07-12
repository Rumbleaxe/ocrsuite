# OCRSuite Logging Guide

OCRSuite uses [loguru](https://github.com/Delgan/loguru) for structured, ISO 8601-compliant logging.

## Overview

- **Console output** — Colorized, concise. Level: INFO (DEBUG with `--verbose`).
- **File output** — Full detail. Level: always DEBUG. ISO 8601 timestamps. 10 MB rotation, 7-day retention.
- **Zero config** — No `setup_logging()` calls needed in modules. `from loguru import logger` and go.

## Log File Location

```
output/<session_dir>/
├── extraction.md
├── figures/
└── log.txt          # ISO 8601 structured log
```

## Log Format

### File (full detail)
```
2026-07-12T11:26:53.027+00:00 | INFO     | ocrsuite.preprocessor:pdf_to_images:53 | Converting 42 pages from book.pdf
2026-07-12T11:27:45.892+00:00 |DEBUG     | ocrsuite.ollama_client:ocr_image:65 | OCR response length: 1423 chars
2026-07-12T11:28:02.140+00:00 | WARNING  | ocrsuite.ollama_client:_call_vision_model:159 | Connection failed, retrying in 2s (attempt 1/3)
```

### Console (colorized)
```
INFO     | ocrsuite.preprocessor:pdf_to_images | Converting 42 pages from book.pdf
ERROR    | ocrsuite.ollama_client:_call_vision_model | Ollama request timed out after 600s
```

## Reading Logs

```powershell
# View live during processing (GUI)
# Click "View Log" button — opens in a new browser tab

# View in terminal
type output\120726_114530\log.txt

# Filter errors only
type output\120726_114530\log.txt | findstr ERROR

# Filter a specific module
type output\120726_114530\log.txt | findstr ollama_client
```

## Structured Analysis

loguru supports JSON serialization for programmatic log analysis:

```python
from loguru import logger

# Add JSON handler for machine-readable logs
logger.add("log.json", format="{message}", serialize=True)
```

This produces JSON lines parsable with `jq` or Python `json.loads()`.
