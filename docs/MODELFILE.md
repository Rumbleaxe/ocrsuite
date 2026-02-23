# DeepSeek-OCR Modelfile Configuration

OCRSuite includes an optimized `Modelfile` for DeepSeek-OCR that configures the model for reliable document OCR processing.

## About the Modelfile

The `Modelfile` is an Ollama configuration file that customizes how the DeepSeek-OCR model behaves. It's similar to a Dockerfile for Ollama models.

**Location:** `./Modelfile`

**Purpose:** Optimize DeepSeek-OCR for:
- Deterministic text extraction (consistent results)
- Handling complex document layouts
- Processing long documents without timeouts
- Preventing hallucinations in OCR output

## Configuration Parameters

### Temperature: 0.0
```
PARAMETER temperature 0.0
```
**Why:** Deterministic output is critical for OCR. Temperature controls randomness - setting it to 0.0 ensures the model makes consistent, reproducible decisions for the same input.

**Impact:** Prevents variations in extracted text, enables reliable verification and validation.

### Context Window: 8192
```
PARAMETER num_ctx 8192
```
**Why:** DeepSeek-OCR can process large documents. Expanding the context window from default 4096 to 8192 tokens allows handling:
- Multi-page document summaries
- Complex layout information
- Longer metadata and structure details

**Impact:** Supports processing of 30+ page documents without truncation.

### Top-p: 0.95
```
PARAMETER top_p 0.95
```
**Why:** Nucleus sampling controls diversity. A value of 0.95 is conservative, reducing hallucinations while maintaining reasonable output quality.

**Impact:** Fewer made-up text insertions or artifacts in OCR output.

### Top-k: 40
```
PARAMETER top_k 40
```
**Why:** Limits sampling to top 40 most likely tokens, preventing unlikely token choices that could corrupt OCR output.

**Impact:** More focused, accurate text extraction.

### Repeat Penalty: 1.1
```
PARAMETER repeat_penalty 1.1
```
**Why:** Penalizes the model for repeating text, common in OCR of repetitive content (headers, page numbers, etc.).

**Impact:** Reduces duplicate lines and repetitive artifacts.

### Token Prediction: 4096
```
PARAMETER num_predict 4096
```
**Why:** Maximum tokens the model generates per OCR task. Balances between supporting long documents and preventing runaway responses.

**Impact:** Prevents the model from generating unlimited output while supporting typical document sizes.

### System Prompt
```
SYSTEM You are an expert OCR assistant. Extract text accurately, preserve layouts and structure, and handle multilingual content. Focus on accuracy over speed.
```
**Why:** Instructs the model on its role and priorities. DeepSeek-OCR is sensitive to system prompts for guiding output quality.

**Impact:** Model focuses on accuracy-first approach, preserving document structure.

## Usage

### Running the Optimized Model

```bash
# Use the optimized ocrsuite-deepseek model (automatically selected by OCRSuite)
ocrsuite process --input document.pdf --output ./output/

# Or explicitly specify it
ocrsuite process --input document.pdf --model ocrsuite-deepseek --output ./output/
```

### Testing the Model Directly

```bash
# Test with an image
ollama run ocrsuite-deepseek "image.jpg\nFree OCR."

# Test with markdown conversion
ollama run ocrsuite-deepseek "image.jpg\n<|grounding|>Convert to markdown."
```

## Performance Tuning

### If Processing is Slow

1. **Reduce num_ctx temporarily:**
   ```bash
   # Create a Modelfile.fast for quick documents
   FROM ocrsuite-deepseek
   PARAMETER num_ctx 4096  # Half the default
   ```
   Then: `ollama create ocrsuite-deepseek-fast -f Modelfile.fast`

2. **Process fewer pages:**
   ```bash
   ocrsuite process --input doc.pdf --max-pages 10 --output ./output/
   ```

3. **Reduce image DPI in config:**
   Edit `ocrsuite.yaml`:
   ```yaml
   pdf:
     dpi: 150  # Instead of 300
   ```

### If Processing Times Out

1. **Increase timeout in config:**
   Edit `ocrsuite.yaml`:
   ```yaml
   ollama:
     timeout: 600  # 10 minutes instead of 5
     model: ocrsuite-deepseek
   ```

2. **Check system resources:**
   - Ensure GPU has ≥8GB VRAM available
   - Check disk space for temporary files
   - Monitor system load (don't run other GPU tasks)

3. **Use different model for specific tasks:**
   ```bash
   # For faster but less accurate OCR:
   ocrsuite process --input doc.pdf --model llama3.2 --output ./output/
   
   # For highest quality (slower):
   ocrsuite process --input doc.pdf --model ocrsuite-deepseek --output ./output/
   ```

## Creating Custom Modelfiles

You can create your own optimized variants:

```bash
# Edit Modelfile for your needs
FROM ocrsuite-deepseek
PARAMETER temperature 0.1  # Slightly more diverse
PARAMETER num_ctx 16384   # Very large documents

# Build it
ollama create my-ocrsuite -f Modelfile

# Use it
ocrsuite process --input doc.pdf --model my-ocrsuite --output ./output/
```

**Parameter Options:**
- `temperature`: 0.0 (deterministic) to 1.0+ (creative)
- `num_ctx`: 1024 to 32768 (context window size)
- `top_p`: 0.0 to 1.0 (nucleus sampling)
- `top_k`: 1 to 40+ (top-k sampling)
- `repeat_penalty`: 1.0 to 1.5 (reduces repetition)

## Troubleshooting

### "Model not found: ocrsuite-deepseek"

The Modelfile hasn't been built yet. Run:
```bash
ollama create ocrsuite-deepseek -f ./Modelfile
```

### "Timeout after 120s" errors

See "If Processing Times Out" section above. The updated default timeout is 300s (5 minutes).

### Poor OCR Quality

1. Try the base `deepseek-ocr:latest` model directly:
   ```bash
   ocrsuite process --input doc.pdf --model deepseek-ocr --output ./output/
   ```

2. Increase `num_ctx` and `num_predict`:
   Edit the Modelfile and rebuild

3. Try a different model:
   ```bash
   ocrsuite process --input doc.pdf --model llava:13b --output ./output/
   ```

## Advanced: Modelfile Syntax

Full Modelfile syntax supported by Ollama:

```
FROM <model>              # Base model to customize
PARAMETER <key> <value>   # Set model parameters
SYSTEM <prompt>           # Set system prompt
TEMPLATE <template>       # Custom chat template (advanced)
LICENSE <text>            # Model license information
MESSAGE <role> <content>  # Multi-turn message example
```

For more details, see: https://github.com/ollama/ollama/blob/main/docs/modelfile.md

## See Also

- [DeepSeek-OCR Official Guide](../DeepSeekOCR_Guide.md)
- [DeepSeek-OCR Local Guide](../DeepSeekOCR_Local_Guide.md)
- [Agentic AI Flow Guide](../AgenticAIFlowForOCR_Guide.md)
- [OCRSuite README](README.md)
- [Ollama Documentation](https://ollama.ai)
