DeepSeek-OCR is a vision-language model specialized for optical character recognition (OCR) and document understanding, excelling in token-efficient processing of images and PDFs with support for layouts, multilingual text, and dynamic resolutions. Official resources and community guides emphasize consistent parameters like temperature=0.0 and specific prompts for optimal accuracy. Below is a comparison of key sources, inferred best practices, and my synthesized detailed guide.

## Key Sources

- **Official GitHub (deepseek-ai/DeepSeek-OCR)**: Primary repo with vLLM and Transformers inference scripts, parameter examples (e.g., ngram_size=30, window_size=90), support modes (tiny to large resolutions), and prompt templates like "<image>\nFree OCR."[^1][^2]
- **Hugging Face Model Card**: Basic inference code using SamplingParams (temperature=0.0, max_tokens=8192) with multi-image batching and multi_modal_data format.[^1]
- **Unsloth Guide (DeepSeek-OCR-2)**: Recommends identical settings (temperature=0.0, ngram_size=30, window_size=90); covers fine-tuning, dynamic resolutions like (0-6)×768×768 + 1×1024×1024, and Transformers/Unsloth code.[^3][^1]
- **DataCamp Hands-On Tutorial**: 7 practical examples (charts, math, multilingual); Gradio app with image preprocessing, error handling, bounding box visualization; tests document-to-Markdown mode.[^4]
- **rdumasia303/deepseek_ocr_app (GitHub)**: Docker-based app with API endpoints (/api/ocr); modes like plain_ocr, describe, find_ref, freeform; supports up to 100MB images.[^2]
- **DeepSeek-OCR Docs (deepseek-ocr.ai)**: API guide (POST /v1/ocr) with file upload, optional prompt/language; Python/JS examples using Bearer token.[^5]
- **SparkCo API Guide**: Details tiny/large/dynamic "Gundam" modes (512×512 to 1280×1280); contextual compression for 30% speed/accuracy gains.[^6]
- **Other**: HF Space demo for tasks like Markdown conversion; Ollama library support.[^7][^8]


## Comparison Table

| Aspect | Official GitHub/HF [^1][^2] | Unsloth [^3][^1] | DataCamp [^4] | App/API Guides [^2][^6][^5] |
| :-- | :-- | :-- | :-- | :-- |
| **Params** | temp=0.0, max_tokens=8192, ngram=30, window=90 | Same + dynamic res | Image resize, token compression | Prompt/language hints, modes (tiny/large) |
| **Inference** | vLLM/Transformers scripts | Unsloth/Transformers + fine-tune | Gradio app w/ bbox viz | Docker API, POST /v1/ocr |
| **Modes** | Native/dynamic res (512-1280) | Dynamic Gundam | Multilingual, Markdown | plain_ocr, describe, freeform |
| **Strengths** | Core code, prompts | Fine-tuning, benchmarks | Real-world tests (7 ex.) | Easy deploy, batch |
| **Limits** | Setup-heavy (CUDA11.8) | OCR-2 focus | No fine-tune | App-specific |

## Best Practices

Use deterministic sampling (temperature=0.0) across all guides for accuracy; pair with ngram_size=30/window_size=90 in vLLM to suppress repetitions [^1][^3][^1][^2]. Select dynamic resolution for complex docs (e.g., Gundam mode segments high-res images) and prompts like "<image>\n<|grounding|>Convert to markdown." for structured output [^6][^2]. Preprocess images (RGB convert, resize if >100MB), handle batches via multi_modal_data, and visualize bounding boxes for verification [^4][^2]. Fine-tune with Unsloth on domain data for 50-80% error reduction [^3][^1]. Run on GPU (A100+ ideal, ~5-10GB model) with flash-attn for speed [^2].

## Detailed Guide

### Installation

Clone the official repo and set up a CUDA 11.8+ env (Python 3.12):

```
git clone https://github.com/deepseek-ai/DeepSeek-OCR.git
cd DeepSeek-OCR
conda create -n deepseek-ocr python=3.12.9 -y && conda activate deepseek-ocr
pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cu118
pip install vllm==0.8.5 flash-attn==2.7.3 -r requirements.txt  # Or transformers for HF [page:3]
```

For Unsloth: `pip install --upgrade unsloth`. Load via Ollama for local: `ollama run deepseek-ocr`.[^8][^3][^1]

### Quick Inference (vLLM - Recommended for Speed)

Use official script or code; edit config.py for paths:[^2]

```
from vllm import LLM, SamplingParams
from vllm.model_executor.models.deepseek_ocr import NGramPerReqLogitsProcessor
from PIL import Image

llm = LLM(model="deepseek-ai/DeepSeek-OCR", logits_processors=[NGramPerReqLogitsProcessor])
image = Image.open("doc.jpg").convert("RGB")
prompt = "<image>\nFree OCR."  # Or "<image>\n<|grounding|>Convert to markdown." [page:3]
inputs = [{"prompt": prompt, "multi_modal_data": {"image": image}}]
params = SamplingParams(temperature=0.0, max_tokens=8192, extra_args=dict(ngram_size=30, window_size=90))
outputs = llm.generate(inputs, params)
print(outputs[^0].outputs[^0].text)
```

For PDFs/images: `python run_dpsk_ocr_pdf.py` (~2500 tokens/s on A100).[^2]

### Transformers Alternative

```
from transformers import AutoModel, AutoTokenizer
import torch
tokenizer = AutoTokenizer.from_pretrained("deepseek-ai/DeepSeek-OCR", trust_remote_code=True)
model = AutoModel.from_pretrained("deepseek-ai/DeepSeek-OCR", trust_remote_code=True, torch_dtype=torch.bfloat16).cuda().eval()
res = model.infer(tokenizer, prompt="<image>\n<|grounding|>OCR this image.", image_file="doc.jpg", base_size=1024, image_size=640, crop_mode=True)  # Dynamic res [page:3]
```

Unsloth variant mirrors this with 1.4x speed.[^3][^1]

### API Usage (Hosted)

POST to /v1/ocr (Bearer auth):[^5]

```python
import requests
files = {'file': open('doc.pdf', 'rb')}
data = {'prompt': 'Extract tables as Markdown', 'language': 'en'}
r = requests.post('https://api.deepseek-ocr.ai/v1/ocr', headers={'Authorization': 'Bearer YOUR_KEY'}, files=files, data=data)
print(r.json()['text'])
```

Apps like rdumasia303 repo: `docker compose up`, POST /api/ocr?mode=plain_ocr.[^2]

### Prompts \& Modes

- Plain text: "<image>\nFree OCR."
- Structured: "<image>\n<|grounding|>Convert the document to markdown."
- Figures: "<image>\nParse the figure."
- Ref: "<image>\nLocate <|ref|>invoice<|/ref|>."
- Multilingual: Auto-detects (e.g., Chinese/Japanese).[^4][^2]
Modes: tiny (512px, low-res), large (1280px, high-fid), Gundam (segmented high-res).[^6][^2]


### Fine-Tuning \& Optimization

Use Unsloth notebook: 40% less VRAM, supports long contexts; e.g., 57-86% CER drop on Persian. Batch process, quantize/prune for edge deploy, GPU batching for throughput.[^9][^1][^3]

### Troubleshooting

- Repetitions: Enforce ngram whitelist (e.g., <td>).[^2]
- OOM: Drop to tiny mode or bfloat16.[^1]
- Test: HF Space or Gradio from DataCamp.[^7][^4]
<span style="display:none">[^10]</span>

<div align="center">⁂</div>

[^1]: https://huggingface.co/deepseek-ai/DeepSeek-OCR

[^2]: https://github.com/rdumasia303/deepseek_ocr_app

[^3]: https://unsloth.ai/docs/models/deepseek-ocr-2

[^4]: https://www.datacamp.com/tutorial/deepseek-ocr-hands-on-guide

[^5]: https://www.deepseek-ocr.ai/docs

[^6]: https://sparkco.ai/blog/deepseek-ocr-api-documentation-advanced-implementation-guide

[^7]: https://huggingface.co/spaces/khang119966/DeepSeek-OCR-DEMO

[^8]: https://ollama.com/library/deepseek-ocr

[^9]: https://sparkco.ai/blog/download-and-implement-deepseek-ocr-model-a-2025-guide

[^10]: https://github.com/deepseek-ai/DeepSeek-OCR/actions

