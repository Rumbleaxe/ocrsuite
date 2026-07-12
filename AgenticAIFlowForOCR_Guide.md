Agentic AI workflows automate multi-step tasks like document processing by chaining LLMs with tools (e.g., OCR for image-to-text, then reasoning/extraction). Guides recommend Ollama for local LLMs (including DeepSeek-OCR) integrated via Python frameworks for privacy and speed. This guide synthesizes libraries, patterns, and a DeepSeek-OCR + Ollama flow for invoice extraction.

## Core Libraries \& Tools

- **Frameworks**: LangGraph (stateful graphs, ReAct loops), LangChain (chains/agents), LlamaIndex (RAG/document AI), Autogen/Agno (multi-agent).[^1][^2][^3][^4][^5][^6]
- **Ollama Integration**: `ollama` Python client for local models; `langchain-ollama` for embeddings/LLMs.[^3][^1]
- **OCR**: `ollama_ocr` package (wraps vision models like DeepSeek-OCR/llava); PaddleOCR for bbox; native DeepSeek-OCR prompts.[^7][^8][^9]
- **Utils**: `Pillow` (images), `PyMuPDF`/`pdf2image` (PDFs), `chromadb`/`faiss` (vector store), `pydantic` (JSON schemas).[^2][^8]
- **Patterns**: ReAct (reason-act-observe), planner-tool-critic; RAG for post-OCR retrieval.[^4][^1][^3]


## Agentic Workflow Patterns

Common flows for OCR: **Ingest → OCR → Parse → Extract → Validate → Output**.

- **ReAct Loop**: LLM plans (e.g., "OCR image"), calls tool, observes, iterates.[^5][^1]
- **Multi-Agent**: OCR agent → Extract agent → Critic (self-correct).[^10][^2]
- **Graph**: Nodes for OCR/extract/verify; edges conditional (e.g., if table detected).[^1]
- Algorithms: Tool-calling (JSON schemas), reflection (critic pass), vector search post-OCR.[^3]


## Setup

1. Install Ollama ≥0.13.0; `ollama pull deepseek-ocr:3b` (OCR) + `ollama pull llama3.2:3b` (reasoner).[^9]
2. Python env: `pip install langgraph langchain-ollama ollama pillow pymupdf ollama-ocr chromadb pydantic`.
3. Run `ollama serve`.

## Detailed Guide: Invoice Processor Agent

Builds a LangGraph agent: Watches dir for images/PDFs, OCRs via DeepSeek-OCR, extracts structured data (amounts, dates), validates, outputs JSON.

### Step 1: Define Tools

```python
from langchain_ollama import OllamaLLM, ChatOllama
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List
import ollama
from ollama_ocr import OCRProcessor  # Or custom DeepSeek [web:20]
from PIL import Image
import fitz  # PyMuPDF

class InvoiceData(BaseModel):
    total: float = Field(description="Invoice total")
    date: str = Field(description="Invoice date")
    items: List[str] = Field(description="Item list")

@tool
def ocr_image(image_path: str) -> str:
    """OCR image/PDF page using DeepSeek-OCR."""
    ocr = OCRProcessor(model_name='deepseek-ocr:3b', base_url="http://localhost:11434")
    text = ocr.extract_text(image_path)  # Returns clean text + layout [web:20][web:23]
    return text

@tool
def extract_invoice(text: str) -> str:
    """Extract structured invoice data."""
    llm = ChatOllama(model="llama3.2:3b", temperature=0.0)
    prompt = f"Extract JSON: {InvoiceData.model_json_schema()}\n\nText: {text}"
    return llm.invoke(prompt).content

@tool
def validate_data(data_json: str) -> str:
    """Critic: Check extraction accuracy."""
    llm = OllamaLLM(model="llama3.2:3b")
    result = llm.invoke(f"Is this valid? Fix errors.\n{data_json}")
    return result
```


### Step 2: Build Agent Graph (LangGraph)

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    input_path: str
    ocr_text: str
    extracted: str
    validated: str
    messages: Annotated[list, operator.add]

def ocr_node(state):
    text = ocr_image(state["input_path"])
    return {"ocr_text": text, "messages": ["OCR done"]}

def extract_node(state):
    data = extract_invoice(state["ocr_text"])
    return {"extracted": data, "messages": ["Extracted"]}

def validate_node(state):
    valid = validate_data(state["extracted"])
    return {"validated": valid, "messages": ["Validated"]}

def router(state):
    if "validated" in state and state["validated"]:
        return "end"
    return "ocr"  # Or conditional

workflow = StateGraph(AgentState)
workflow.add_node("ocr", ocr_node)
workflow.add_node("extract", extract_node)
workflow.add_node("validate", validate_node)
workflow.set_entry_point("ocr")
workflow.add_conditional_edges("ocr", lambda s: "extract", {"extract": "extract"})
workflow.add_conditional_edges("extract", lambda s: "validate")
workflow.add_conditional_edges("validate", router, {"end": END, "ocr": "ocr"})
app = workflow.compile()
```


### Step 3: Run Workflow

```python
result = app.invoke({"input_path": "invoice.jpg"})
print(result["validated"])  # JSON output [web:18]
```

- PDF handling: Loop `fitz.open(pdf).get_pixmap().tobytes("png")` to images.[^8]
- Dir watch: Use `watchdog` lib for auto-trigger.


### Step 4: Enhancements

- **RAG**: Embed OCR text to ChromaDB; query for "find total".[^3]
- **Multi-Agent**: Separate OCR/Extract agents via Autogen.[^2]
- **Self-Correct**: Add reflection edge if validation fails.[^5]
- **Eval**: Test on 10 invoices; score JSON parse rate.[^1]
- Params: Temp=0.0 everywhere; max_iter=5.[^9][^1]

This flow processes 100s of docs offline (~10s/invoice on RTX); extend with web search tool for verification.[^7][^2][^9][^1]

<div align="center">⁂</div>

[^1]: https://adspyder.io/blog/agentic-ai-with-ollama/

[^2]: https://www.youtube.com/watch?v=-C8vWRedgLs

[^3]: https://www.youtube.com/watch?v=E4l91XKQSgw

[^4]: https://www.llamaindex.ai/blog/document-ai-the-next-evolution-of-intelligent-document-processing

[^5]: https://www.youtube.com/watch?v=UiK6ln_Qh7E

[^6]: https://www.youtube.com/watch?v=22CJYVSdbjQ

[^7]: https://github.com/imanoop7/Ollama-OCR

[^8]: https://damimartinez.github.io/building-agentic-document-understanding-with-ocr-and-llms/

[^9]: https://ollama.com/library/deepseek-ocr:latest

[^10]: https://paulabartabajo.substack.com/p/lets-build-a-local-agentic-workflow

