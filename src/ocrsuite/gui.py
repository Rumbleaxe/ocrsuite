"""OCRSuite GUI — NiceGUI app for interactive PDF processing.

Commands:
    ocrsuite-gui              Browser at http://localhost:8080
    ocrsuite-gui --native     Desktop window (requires pywebview)
"""

import asyncio
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from loguru import logger
from nicegui import app, ui

from .assembler import OutputAssembler
from .config import Config
from .ollama_client import OllamaClient
from .preprocessor import PDFPreprocessor
from .utils import init_logging

# ── Brand ─────────────────────────────────────────────────
TECH_BLUE = "#0066FF"
CYBER_CYAN = "#00D9FF"
DARK_BG = "#0A0A0F"
SURFACE = "#12121A"
SURFACE_HOVER = "#1A1A2A"
TEXT = "#E2E5EA"
MUTED = "#8892A4"
GREEN = "#22C55E"
RED = "#EF4444"
BORDER = "#1E2130"

# ── Shared mutable state (bridges thread pool -> UI polling) ──
class Progress:
    def __init__(self):
        self.reset()

    def reset(self):
        self.phase: str = "idle"
        self.preprocess_s: float = 0
        self.page_current: int = 0
        self.page_total: int = 0
        self.pages_done: int = 0
        self.ollama_elapsed_s: float = 0
        self.ollama_avg_s: float = 0
        self.ollama_timeout: int = 600
        self.errors: list[str] = []
        self.output_files: list[dict] = []
        self.log_path: Optional[Path] = None

progress = Progress()
processing = False
uploaded_pdf: Optional[Path] = None
session_dir: Optional[Path] = None

# ── Ollama helpers ────────────────────────────────────────
def _ollama_healthy() -> bool:
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        return r.ok
    except Exception:
        return False


def _ollama_models() -> list[str]:
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        if r.ok:
            return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return ["ocrsuite-deepseek"]


# ── Pipeline (runs in asyncio.to_thread) ──────────────────
def run_pipeline(pdf_path: Path, cfg: Config, out_dir: Path):
    global processing, progress
    progress.reset()
    processing = True
    progress.phase = "preprocessing"

    log_file = init_logging(out_dir, verbose=cfg.output.debug_mode)
    progress.log_path = log_file
    temp_dir = out_dir / ".temp_images"

    try:
        # ── Preprocessing ──
        t0 = time.monotonic()
        preprocessor = PDFPreprocessor(dpi=cfg.pdf.dpi)
        info = preprocessor.get_pdf_info(pdf_path)
        pages_to_process = info["page_count"]
        if cfg.pdf.max_pages:
            pages_to_process = min(cfg.pdf.max_pages, pages_to_process)

        progress.page_total = pages_to_process
        images = preprocessor.pdf_to_images(pdf_path, temp_dir, max_pages=cfg.pdf.max_pages)
        progress.preprocess_s = round(time.monotonic() - t0, 1)

        # ── OCR ──
        progress.phase = "ocr"
        client = OllamaClient(cfg.ollama)
        assembler = OutputAssembler(out_dir, source_filename=pdf_path.stem, debug=cfg.output.debug_mode)

        extracted: list[dict] = []
        total_s = 0.0
        n_req = 0

        for i, img in enumerate(images):
            progress.page_current = i + 1
            t_ocr = time.monotonic()

            try:
                text = client.ocr_image(img)
                ok = text and text.strip() and "[Unrecognized" not in text
                extracted.append({
                    "page": img.stem,
                    "type": "text" if ok else "unknown",
                    "content": text.strip() if text.strip() else "[Empty page]",
                })
                assembler.increment_pages()
            except Exception as e:
                progress.errors.append(f"{img.name}: {e}")
                assembler.record_error(f"{img.name}: {e}")

            elapsed = time.monotonic() - t_ocr
            progress.ollama_elapsed_s = round(elapsed, 1)
            total_s += elapsed
            n_req += 1
            progress.ollama_avg_s = round(total_s / n_req, 1)
            progress.ollama_timeout = cfg.ollama.timeout
            progress.pages_done = i + 1

        # ── Assembly ──
        progress.phase = "assembly"
        md = "\n\n".join(
            f"## {item['page']} ({item['type']})\n\n{item['content']}"
            for item in extracted
        )
        assembler.save_markdown(md, title=pdf_path.stem.replace("_", " ").title())

        # ── Post-processing (optional) ──
        if cfg.postprocess.enabled:
            progress.phase = "postprocess"
            try:
                from .config import OllamaConfig as OC
                from .postprocessor import PostProcessor

                pp_client = OllamaClient(
                    OC(
                        url=cfg.ollama.url,
                        model=cfg.postprocess.model,
                        timeout=cfg.ollama.timeout,
                        max_retries=cfg.ollama.max_retries,
                    )
                )
                processor = PostProcessor(
                    pp_client,
                    ascii_width=cfg.postprocess.ascii_width,
                    canny_low=cfg.postprocess.canny_low,
                    canny_high=cfg.postprocess.canny_high,
                )

                figures_dir = (
                    assembler.figures_dir
                    if assembler.figures_dir and assembler.figures_dir.exists()
                    else None
                )
                md_output = out_dir / assembler.get_output_filename()
                enriched = processor.postprocess(md_output, figures_dir or out_dir)

                pp_path = out_dir / f"postprocessed_{md_output.name}"
                pp_path.write_text(enriched, encoding="utf-8")

            except Exception as e:
                logger.warning(f"Post-processing failed: {e}")
                progress.errors.append(f"postprocess: {e}")

        files = []
        for f in sorted(out_dir.iterdir()):
            if f.is_file() and f.name != "log.txt":
                files.append({"name": f.name, "size_kb": round(f.stat().st_size / 1024, 1)})
        files.sort(key=lambda x: (not x["name"].endswith(".md"), x["name"]))
        progress.output_files = files

    except Exception as e:
        progress.errors.append(str(e))

    finally:
        if not cfg.output.debug_mode and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
        progress.phase = "done"
        processing = False


# ── Log route ─────────────────────────────────────────────
@app.get("/log")
def log_route():
    from starlette.responses import PlainTextResponse, Response

    if progress.log_path and progress.log_path.exists():
        return PlainTextResponse(progress.log_path.read_text(encoding="utf-8"))
    return Response("No log available yet.", status_code=404)


# ── Main page ─────────────────────────────────────────────
@ui.page("/")
def index():
    ui.add_head_html(f"""
    <style>
      body {{ background: {DARK_BG} !important; }}
      .phase-row {{ display: flex; align-items: center; gap: 8px; padding: 5px 0; }}
      .dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
      .dot-done {{ background: {GREEN}; }}
      .dot-on  {{ background: {TECH_BLUE}; animation: pulse 1.4s infinite; }}
      .dot-off {{ background: #2A2A40; }}
      .dot-red {{ background: {RED}; }}
      @keyframes pulse {{ 0%,100% {{ opacity: 1 }} 50% {{ opacity: 0.25 }} }}
      .file-row {{ display: flex; align-items: center; justify-content: space-between;
                   padding: 6px 0; border-bottom: 1px solid {BORDER}; }}
      .dropzone {{
        border: 2px dashed {MUTED}; border-radius: 8px; padding: 28px 16px;
        text-align: center; transition: border-color 0.2s;
      }}
      .dropzone-has-file {{ border-color: {GREEN}; border-style: solid; padding: 12px 16px; }}
    </style>
    """)

    dark = ui.dark_mode()
    dark.value = True

    # ── Header ──
    with ui.row().classes("w-full items-center justify-between px-2 py-3"):
        with ui.row().classes("items-center gap-3"):
            ui.label("OCRSuite").classes(f"text-xl font-bold text-[{TEXT}]")
            ui.label("local document processing").classes(f"text-xs text-[{MUTED}]")
        with ui.row().classes("items-center gap-4"):
            health_dot = ui.html(f'<span class="dot dot-off" style="background:{RED}"></span>')
            health_lbl = ui.label("Ollama: checking…").classes(f"text-sm text-[{MUTED}]")
        ui.button(icon="dark_mode", on_click=lambda: dark.toggle()).props("flat round dense")

    # ── Health check on load ──
    async def _check_health():
        ok = await asyncio.to_thread(_ollama_healthy)
        if ok:
            health_dot.content = f'<span class="dot dot-done"></span>'
            health_lbl.set_text("Ollama running")
            process_btn.enable()
        else:
            health_dot.content = f'<span class="dot dot-red"></span>'
            health_lbl.set_text("Ollama not detected — start with: ollama serve")
            process_btn.disable()

    asyncio.ensure_future(_check_health())

    # ═══════════════════════════════════════════════════════
    # 1 — UPLOAD
    # ═══════════════════════════════════════════════════════
    with ui.card().classes(f"w-full bg-[{SURFACE}] p-4 rounded-lg"):
        ui.label("Upload PDF").classes(f"text-sm font-semibold text-[{TEXT}] mb-3")

        file_info = ui.label("Select a file to begin").classes(f"text-xs text-[{MUTED}]")

        async def handle_upload(e):
            global uploaded_pdf
            try:
                path = Path(tempfile.gettempdir()) / f"ocrsuite_{e.file.name}"
                await e.file.save(str(path))
                uploaded_pdf = path

                try:
                    from .preprocessor import PDFPreprocessor
                    pinfo = PDFPreprocessor().get_pdf_info(uploaded_pdf)
                    page_count = pinfo["page_count"]
                except Exception:
                    page_count = "?"

                size_mb = e.file.size() / (1024 * 1024)
                file_info.set_text(f"{e.file.name}  —  {size_mb:.1f} MB · {page_count} pages")
                file_info.classes(f"text-sm text-[{GREEN}]")

                if not processing:
                    process_btn.enable()
            except Exception:
                ui.notify("Upload failed. Try again.", type="negative")

        ui.upload(
            on_upload=handle_upload,
            label="Choose PDF or drag here",
            auto_upload=True,
        ).props("accept=.pdf color=blue-6").classes("w-full")

    # ═══════════════════════════════════════════════════════
    # 2 — SETTINGS
    # ═══════════════════════════════════════════════════════
    with ui.card().classes(f"w-full bg-[{SURFACE}] p-4 rounded-lg mt-3"):
        ui.label("Settings").classes(f"text-sm font-semibold text-[{TEXT}] mb-3")

        with ui.row().classes("w-full gap-4 items-end flex-wrap"):
            models = _ollama_models()
            msel = ui.select(
                label="Model",
                options=models,
                value=models[0] if models else "ocrsuite-deepseek",
            ).classes("w-56").props("outlined dense bg-color=dark")

            dpi = ui.slider(min=72, max=600, value=300, step=25).props("label label-always switch-label-side dense")
            ui.label("DPI").classes(f"text-xs text-[{MUTED}] mb-3")

            mpages = ui.select(
                label="Max Pages",
                options={"All": None, 5: 5, 10: 10, 20: 20, 50: 50, 100: 100},
                value=None,
            ).classes("w-28").props("outlined dense bg-color=dark")

            debug_cb = ui.checkbox("Debug", value=False).props("dense")

        with ui.expansion("Advanced").props("dense").classes("w-full mt-2"):
            post_cb = ui.checkbox("Post-process with vision model", value=False)
            post_lbl = ui.label(
                "Enrich OCR output: tables, links, ASCII art from figures"
            ).classes(f"text-xs text-[{MUTED}] ml-6")
            post_model = ui.select(
                label="Vision model",
                options=[
                    m for m in models
                    if any(v in m.lower() for v in ("llava", "vision", "bakllava", "granite"))
                ] or ["llava:13b"],
                value="llava:13b",
            ).classes("w-56").props("outlined dense bg-color=dark")

    # ═══════════════════════════════════════════════════════
    # 3 — PROCESS BUTTON
    # ═══════════════════════════════════════════════════════
    async def start():
        global uploaded_pdf, processing, session_dir, progress
        if not uploaded_pdf or processing:
            return

        cfg = Config()
        cfg.ollama.model = msel.value
        cfg.pdf.dpi = int(dpi.value)
        cfg.pdf.max_pages = mpages.value
        cfg.output.debug_mode = bool(debug_cb.value)
        cfg.postprocess.enabled = bool(post_cb.value)
        if post_cb.value:
            cfg.postprocess.model = post_model.value

        session_dir = (
            Path(__file__).parent.parent.parent
            / "output"
            / datetime.now().strftime("%d%m%y_%H%M%S")
        )
        session_dir.mkdir(parents=True, exist_ok=True)
        progress.log_path = session_dir / "log.txt"

        process_btn.disable()
        process_btn.set_text("Processing…")
        await asyncio.to_thread(run_pipeline, uploaded_pdf, cfg, session_dir)
        process_btn.set_text("Process Another")
        process_btn.enable()

    process_btn = ui.button(
        "Process Document", on_click=lambda: asyncio.ensure_future(start())
    )
    process_btn.props('color="blue-6" size="md"')
    process_btn.classes("w-full mt-4")
    process_btn.disable()

    # ═══════════════════════════════════════════════════════
    # 4 — PIPELINE STATUS
    # ═══════════════════════════════════════════════════════
    status_card = ui.card().classes(f"w-full bg-[{SURFACE}] p-4 rounded-lg mt-3")

    with status_card:
        ui.label("Pipeline Status").classes(f"text-sm font-semibold text-[{TEXT}] mb-3")

        pre_row = ui.html(
            f'<div class="phase-row"><span class="dot dot-off"></span> '
            f'<span style="color:{MUTED};font-size:13px">Preprocessing</span></div>'
        )
        ocr_row = ui.html(
            f'<div class="phase-row"><span class="dot dot-off"></span> '
            f'<span style="color:{MUTED};font-size:13px">OCR Extraction</span></div>'
        )
        asm_row = ui.html(
            f'<div class="phase-row"><span class="dot dot-off"></span> '
            f'<span style="color:{MUTED};font-size:13px">Assembly</span></div>'
        )
        pp_row = ui.html(
            f'<div class="phase-row"><span class="dot dot-off"></span> '
            f'<span style="color:{MUTED};font-size:13px">Post-processing</span></div>'
        )

        page_prog = ui.linear_progress(0).props("rounded").classes("w-full mt-3")
        page_lbl = ui.label("").classes(f"text-xs text-[{MUTED}] mt-1")

        ollama_prog = ui.linear_progress(0).props("rounded color=cyan-6").classes("w-full mt-3")
        ollama_lbl = ui.label("").classes(f"text-xs text-[{MUTED}] mt-1")

        log_btn = ui.button("View Log", on_click=lambda: ui.open("/log"))
        log_btn.props("flat size=sm color=grey-6").classes("hidden mt-2")

    # ═══════════════════════════════════════════════════════
    # 5 — OUTPUT
    # ═══════════════════════════════════════════════════════
    out_card = ui.card().classes(f"w-full bg-[{SURFACE}] p-4 rounded-lg mt-3")

    with out_card:
        ui.label("Output").classes(f"text-sm font-semibold text-[{TEXT}] mb-2")
        out_col = ui.column().classes("w-full gap-0")
        with out_col:
            ui.label("Ready. Upload a PDF and press Process.").classes(f"text-xs text-[{MUTED}]")

    # ═══════════════════════════════════════════════════════
    # POLLING (300ms)
    # ═══════════════════════════════════════════════════════
    def _phase_for(name: str, label: str, current: int, row: ui.html) -> None:
        """Update a phase row with the correct dot and label."""
        idx = {"preprocessing": 1, "ocr": 2, "assembly": 3, "postprocess": 4}.get(name, 0)
        color = MUTED
        dot_cls = "dot-off"
        text = label

        if name == "preprocessing" and progress.preprocess_s > 0:
            text = f"Preprocessing — {progress.preprocess_s}s"

        if current > idx:
            dot_cls = "dot-done"
            color = GREEN
        elif current == idx:
            dot_cls = "dot-on"
            color = TECH_BLUE
        elif current == 5:
            dot_cls = "dot-done"
            color = GREEN

        row.content = (
            f'<div class="phase-row">'
            f'<span class="dot {dot_cls}"></span>'
            f'<span style="color:{color};font-size:13px">{text}</span>'
            f"</div>"
        )

    def poll():
        phase_map = {"idle": 0, "preprocessing": 1, "ocr": 2, "assembly": 3, "postprocess": 4, "done": 5}
        current = phase_map.get(progress.phase, 0)

        _phase_for("preprocessing", "Preprocessing", current, pre_row)
        _phase_for("ocr", "OCR Extraction", current, ocr_row)
        _phase_for("assembly", "Assembly", current, asm_row)
        _phase_for("postprocess", "Post-processing", current, pp_row)

        # ── Page progress ──
        if progress.page_total > 0:
            ratio = progress.pages_done / progress.page_total
            page_prog.value = ratio
            page_lbl.set_text(
                f"{progress.pages_done} / {progress.page_total} pages  ({int(ratio * 100)}%)"
            )
        else:
            page_prog.value = 0
            page_lbl.set_text("")

        # ── Ollama per-page progress (bottleneck finder) ──
        if progress.phase == "ocr" and progress.ollama_elapsed_s > 0:
            ratio = min(progress.ollama_elapsed_s / progress.ollama_timeout, 1.0)
            ollama_prog.value = ratio
            remaining = progress.ollama_avg_s * (progress.page_total - progress.pages_done)
            m, s = int(remaining // 60), int(remaining % 60)
            ollama_lbl.set_text(
                f"Page {progress.page_current}: {progress.ollama_elapsed_s:.0f}s / "
                f"{progress.ollama_timeout}s timeout  "
                f"(~{progress.ollama_avg_s:.0f}s/page avg, {m}m {s}s remaining)"
            )
        else:
            ollama_prog.value = 0
            ollama_lbl.set_text("")

        # ── Log button ──
        if current in (1, 2, 3, 4):
            log_btn.classes(remove="hidden")
        else:
            log_btn.classes("hidden")

        # ── Output files (lazy: only update on state change) ──
        if progress.phase == "done":
            out_col.clear()
            with out_col:
                if progress.errors and not progress.output_files:
                    ui.label("Processing failed with errors:").classes(f"text-sm text-[{RED}] mb-2")
                    for e in progress.errors:
                        ui.label(f"• {e}").classes(f"text-xs text-[{MUTED}]")
                elif progress.output_files:
                    for f in progress.output_files:
                        fpath = str(session_dir / f["name"]) if session_dir else ""
                        with ui.row().classes("file-row w-full"):
                            ui.label(f'{f["name"]}  ({f["size_kb"]} KB)').classes(f"text-sm text-[{TEXT}]")
                            dl = ui.button("Download", on_click=lambda _, p=fpath: ui.download(p))
                            dl.props("flat size=sm color=blue-6 dense")

    ui.timer(0.3, poll)


# ── Entry point ───────────────────────────────────────────
def main():
    import sys

    native = "--native" in sys.argv
    ui.run(
        title="OCRSuite",
        host="127.0.0.1",
        port=8080,
        dark=True,
        native=native,
        reload=False,
        show=False if native else True,
    )
