DeepSeek-OCR runs locally via Ollama as a 3B vision-language model (6.7GB quantized), ideal for GPU setups (8GB+ VRAM recommended) with excellent OCR on images/PDFs using multimodal prompts. It requires Ollama v0.13.0+ and supports deterministic text extraction with layout awareness. This guide covers setup, optimal configs, prompts, and examples for reliable local use.

## Prerequisites

- Hardware: NVIDIA GPU (RTX 30xx+ or A100 equiv.), 8GB+ VRAM; CPU fallback slow.
- OS: Linux/Mac/Windows (WSL2 for Win).
- Install Ollama: Download from ollama.com/download; verify `ollama --version` ≥0.13.0.[^1][^2]
- Python (optional): For API/scripts, `pip install ollama pillow`.


## Installation \& Model Pull

1. Start Ollama service: `ollama serve` (runs on http://localhost:11434).
2. Pull model: `ollama pull deepseek-ocr:3b` (or `deepseek-ocr:latest`, same 6.7GB/8K ctx).[^3][^2][^1]
    - Downloads ~6.7GB; list with `ollama list`.
3. Test run: `ollama run deepseek-ocr`.[^2]

## Optimal Configuration

Ollama handles most params internally, but tune via Modelfile or API for best results:

- **Temperature**: 0.0 (deterministic; default ~0.8 too random).[^3]
- **Top-p/Top-k**: 0.95/40 (reduces hallucinations).
- **Max tokens**: 4096-8192 (covers long docs; 8K ctx limit).[^2]
- **Repeat penalty**: 1.1 (avoids loops).
- **Vision params**: Auto-handles images; use `num_ctx=8192` for large inputs.
- Custom Modelfile (create `Modelfile`, edit, `ollama create deepseek-ocr-custom -f Modelfile`):

```
FROM deepseek-ocr:3b
PARAMETER temperature 0.0
PARAMETER top_p 0.95
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 8192
```

Run: `ollama run deepseek-ocr-custom`.[^1]

Host config: Edit `~/.ollama/config` for GPU layers (e.g., `OLLAMA_NUM_GPU_LAYERS=35` for full offload).[^4][^3]

## Best Prompts

Model is prompt-sensitive—use exact templates with newlines/punctuation. Defaults to English; specify lang if needed.[^3][^2]


| Task | Prompt Template | Use Case/Example |
| :-- | :-- | :-- |
| Free OCR | `/path/to/image\nFree OCR.` | Basic text extraction [^2]. |
| Layout Markdown | `/path/to/image\n<\|grounding\|>Convert the document to markdown.` | Tables/forms to MD [^2]. |
| Figure Parse | `/path/to/image\nParse the figure.` | Charts/graphs [^2]. |
| Plain Extract | `/path/to/image\nExtract the text in the image.` | Clean text, no layout [^2]. |
| Grounded Loc | `/path/to/image\n<\|grounding\|>Locate <\|ref\|>invoice<\|/ref\|>.` | Specific elements [^3]. |
| Multilingual | `/path/to/image\nFree OCR. (Greek text)` | Add lang hint [^4]. |

CLI: `ollama run deepseek-ocr "/path/to/image.jpg\n<|grounding|>Convert to markdown."` (escapes for shell) [^2].

## CLI Usage

- Single image: `ollama run deepseek-ocr "image.jpg\nFree OCR."`.
- Batch: Script loop over files.
- Output: Streams text; pipe to file `> output.txt`.
Example:

```
ollama run deepseek-ocr-custom "doc.png\nParse the figure."
```

Expect: Accurate text + bounding hints; ~5-20s/inference on RTX 4070.[^3]

## Python API Guide

Install `pip install ollama pillow requests`.

```python
import ollama
from PIL import Image
import base64

# Encode image
def img_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

response = ollama.chat(
    model='deepseek-ocr:3b',  # Or custom
    messages=[{
        'role': 'user',
        'content': 'Free OCR.',
        'images': [img_to_base64('doc.jpg')]  # Multimodal [page:1]
    }],
    options={
        'temperature': 0.0,
        'top_p': 0.95,
        'num_predict': 4096  # Max tokens
    }
)
print(response['message']['content'])
```

For Upsonic lib (OCR-focused): `pip install upsonic-ocr`, then:

```python
from upsonic.ocr import OCR
from upsonic.ocr.layer_1.engines import DeepSeekOllamaOCREngine

engine = DeepSeekOllamaOCREngine(
    host="http://localhost:11434",
    model="deepseek-ocr:3b",
    prompt="<image>\nFree OCR.",  # Custom
    rotation_fix=True  # Auto-rotate
)
ocr = OCR(layer_1_ocr_engine=engine)
text = ocr.get_text('doc.pdf')  # Handles PDFs too [web:11][page:2]
print(text)
```


## Advanced Tips \& Best Practices

- **Preprocessing**: RGB convert (`PIL.Image.open().convert('RGB')`), resize >512px if blurry; avoid >4K res (OOM).
- **Batch**: API supports multi-images in `images` list.
- **Privacy/Speed**: Fully local, no API keys; ~2-5x slower than vLLM but CPU viable.[^5]
- **Fine-tune**: Not native; export to HF for LoRA via Unsloth [previous context].
- **Troubleshoot**:
    - No vision: Update Ollama, check GPU `nvidia-smi`.
    - Repetitions: Lower temp, add penalty.
    - Errors: Punct/newline exact; test prompts from Ollama page.[^2]
    - Monitor: `ollama ps`; `OLLAMA_DEBUG=1` for logs.
- Benchmarks: 95%+ acc on printed text; weak on handwriting.[^6]

This setup yields production-ready local OCR; scale with Docker/Ollama API server.[^4][^1][^2][^3]
<span style="display:none">[^10][^11][^12][^13][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://ollama.com/library/deepseek-ocr

[^2]: https://huggingface.co/deepseek-ai/DeepSeek-OCR

[^3]: https://docs.upsonic.ai/concepts/ocr/providers/deepseek-ocr-ollama

[^4]: https://unsloth.ai/docs/models/deepseek-ocr-2

[^5]: https://sparkco.ai/blog/download-and-implement-deepseek-ocr-model-a-2025-guide

[^6]: https://blog.codeminer42.com/exploring-deepseek-ocr-how-well-can-it-read-images/

[^7]: https://www.datacamp.com/de/tutorial/deepseek-r1-ollama

[^8]: https://www.datacamp.com/tutorial/deepseek-r1-ollama

[^9]: https://www.datacamp.com/tutorial/deepseek-ocr-hands-on-guide

[^10]: https://www.youtube.com/watch?v=lTiMnfgp__o

[^11]: https://www.deepseek-ocr.ai/docs

[^12]: https://upsonic.mintlify.app/concepts/ocr/providers/deepseek-ocr-ollama

[^13]: https://www.reddit.com/r/ollama/comments/1pb7la3/deepseekocr_in_ollama_questions/

