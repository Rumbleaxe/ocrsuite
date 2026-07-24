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

# ── CSS ───────────────────────────────────────────────────
CSS = """\
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; }

  :root, html[data-theme="dark"] {
    --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --bg: #282828;
    --surface: #32302f;
    --surface-hover: #3c3836;
    --surface-alt: #1d2021;
    --border: #504945;
    --border-light: #3c3836;
    --text-primary: #ebdbb2;
    --text-secondary: #a89984;
    --text-heading: #fbf1c7;
    --text-link: #83a598;
    --primary: #d79921;
    --primary-hover: #fabd2f;
    --primary-text: #1d2021;
    --accent: #fe8019;
    --success: #b8bb26;
    --success-dim: #79740e;
    --error: #fb4934;
    --warning: #fabd2f;
    --info: #83a598;
    --info-dim: #458588;
    --ring: #d79921;
    --radius: 10px;
    --radius-sm: 6px;
    --shadow: 0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2);
    --shadow-lg: 0 4px 12px rgba(0,0,0,0.4);
    --transition: 180ms ease;
  }

  html[data-theme="light"] {
    --bg: #fbf1c7;
    --surface: #f2e5bc;
    --surface-hover: #ebdbb2;
    --surface-alt: #f9f0d5;
    --border: #d5c4a1;
    --border-light: #ebdbb2;
    --text-primary: #3c3836;
    --text-secondary: #665c54;
    --text-heading: #282828;
    --text-link: #076678;
    --primary: #b57614;
    --primary-hover: #af3a03;
    --primary-text: #fbf1c7;
    --accent: #af3a03;
    --success: #79740e;
    --success-dim: #98971a;
    --error: #9d0006;
    --warning: #b57614;
    --info: #076678;
    --info-dim: #458588;
    --ring: #b57614;
    --shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
    --shadow-lg: 0 4px 12px rgba(0,0,0,0.12);
  }

  body {
    margin: 0; padding: 0;
    font-family: var(--font);
    background: var(--bg);
    color: var(--text-primary);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  /* ── Theme transition ── */
  body, body * {
    transition: background-color var(--transition), color var(--transition), border-color var(--transition), box-shadow var(--transition);
  }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--text-secondary); }

  /* ── Utility classes ── */
  .card-ocr {
    background: var(--surface);
    border: 1px solid var(--border-light);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    overflow: hidden;
  }
  .card-ocr:hover {
    border-color: var(--border);
  }

  .phase-row {
    display: flex; align-items: center; gap: 10px; padding: 6px 0;
  }
  .dot {
    width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
    transition: background-color 0.3s ease;
  }
  .dot-done { background: var(--success); }
  .dot-on  { background: var(--primary); animation: pulse 1.4s infinite; }
  .dot-off { background: var(--border); opacity: 0.5; }
  .dot-red { background: var(--error); }

  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.25; } }

  .file-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 8px 0; border-bottom: 1px solid var(--border-light);
    transition: background-color var(--transition);
  }
  .file-row:last-child { border-bottom: none; }
  .file-row:hover { background: var(--surface-hover); margin: 0 -12px; padding: 8px 12px; border-radius: var(--radius-sm); }

  .dropzone {
    border: 2px dashed var(--border);
    border-radius: var(--radius);
    padding: 32px 16px;
    text-align: center;
    transition: all var(--transition);
    background: var(--surface-alt);
  }
  .dropzone-has-file {
    border-color: var(--success); border-style: solid; padding: 14px 16px;
    background: var(--surface);
  }

  /* ── Empty state ── */
  .empty-state { text-align: center; padding: 32px 20px 24px; }
  .empty-steps { display: flex; gap: 24px; justify-content: center; flex-wrap: wrap; margin-top: 20px; }
  .empty-step {
    display: flex; flex-direction: column; align-items: center; gap: 8px;
    width: 100px; text-align: center;
  }
  .empty-step-icon {
    width: 40px; height: 40px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; font-weight: 700;
  }

  /* ── Summary card ── */
  .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; }
  .summary-item { text-align: center; padding: 12px 8px; background: var(--surface-alt); border-radius: var(--radius-sm); }
  .summary-value { font-size: 20px; font-weight: 700; font-family: var(--font); }

  /* ── Log viewer ── */
  .log-viewer {
    background: var(--surface-alt);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-sm);
    padding: 12px 16px;
    max-height: 320px;
    overflow-y: auto;
    font-family: 'Cascadia Code', 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 12px;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-all;
  }

  /* ── Session history ── */
  .session-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 12px;
    border: 1px solid var(--border-light);
    border-radius: var(--radius-sm);
    margin-bottom: 8px;
    transition: all var(--transition);
    cursor: pointer;
  }
  .session-row:hover { border-color: var(--border); background: var(--surface-alt); }

  /* ── Status bar ── */
  .status-bar {
    display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
    padding: 8px 16px;
    background: var(--surface-alt);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-sm);
    font-size: 12px;
  }
  .status-item { display: flex; align-items: center; gap: 6px; }

  /* ── Quasar brand colors ── */
  :root, html[data-theme="dark"] {
    --q-primary: #d79921;
    --q-secondary: #458588;
    --q-accent: #fe8019;
    --q-positive: #b8bb26;
    --q-negative: #fb4934;
    --q-info: #83a598;
    --q-warning: #fabd2f;
  }
  html[data-theme="light"] {
    --q-primary: #b57614;
    --q-secondary: #076678;
    --q-accent: #af3a03;
    --q-positive: #79740e;
    --q-negative: #9d0006;
    --q-info: #076678;
    --q-warning: #b57614;
  }

  /* ── Quasar component overrides ── */
  .q-field--outlined .q-field__control { color: var(--text-primary); }
  .q-field__native, .q-field__label { color: var(--text-secondary) !important; }
  .q-checkbox__label { color: var(--text-primary); }
  .q-expansion-item .q-item__label { color: var(--text-primary); }
</style>
"""


# ── Shared mutable state ──────────────────────────────────
class Progress:
    def __init__(self):
        self.reset()

    def reset(self):
        self.phase: str = "idle"
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.preprocess_s: float = 0.0
        self.page_current: int = 0
        self.page_total: int = 0
        self.pages_done: int = 0
        self.pages_successful: int = 0
        self.ollama_elapsed_s: float = 0.0
        self.ollama_avg_s: float = 0.0
        self.ollama_timeout: int = 600
        self.errors: list[str] = []
        self.output_files: list[dict] = []
        self.log_path: Optional[Path] = None
        self.summary_shown: bool = False


progress = Progress()
processing = False
uploaded_pdf: Optional[Path] = None
session_dir: Optional[Path] = None

# ── Helpers ───────────────────────────────────────────────
OUTPUT_ROOT = Path(__file__).parent.parent.parent / "output"


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


def _ollama_version() -> str:
    try:
        r = requests.get("http://localhost:11434/api/version", timeout=2)
        if r.ok:
            return r.json().get("version", "unknown")
    except Exception:
        pass
    return "not detected"


def _disk_usage_str() -> str:
    try:
        usage = shutil.disk_usage(OUTPUT_ROOT if OUTPUT_ROOT.exists() else Path.cwd())
        free_gb = usage.free / (1024**3)
        if free_gb >= 1:
            return f"{free_gb:.1f} GB free"
        return f"{free_gb * 1024:.0f} MB free"
    except Exception:
        return "unknown"


def _scan_sessions() -> list[dict]:
    sessions = []
    if not OUTPUT_ROOT.exists():
        return sessions
    for entry in sorted(OUTPUT_ROOT.iterdir(), reverse=True):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        try:
            ts = datetime.strptime(entry.name, "%d%m%y_%H%M%S")
        except ValueError:
            continue
        files = []
        total_kb = 0
        for f in sorted(entry.iterdir()):
            if f.is_file() and f.name != "log.txt":
                size_kb = round(f.stat().st_size / 1024, 1)
                total_kb += size_kb
                files.append({"name": f.name, "size_kb": size_kb})
        sessions.append(
            {
                "id": entry.name,
                "timestamp": ts,
                "path": entry,
                "files": files,
                "file_count": len(files),
                "total_kb": round(total_kb, 1),
            }
        )
    return sessions


# ── Pipeline (runs in asyncio.to_thread) ──────────────────
def run_pipeline(pdf_path: Path, cfg: Config, out_dir: Path):
    global processing, progress
    progress.reset()
    processing = True
    progress.start_time = time.monotonic()
    progress.phase = "preprocessing"

    log_file = init_logging(out_dir, verbose=cfg.output.debug_mode)
    progress.log_path = log_file
    temp_dir = out_dir / ".temp_images"

    try:
        t0 = time.monotonic()
        preprocessor = PDFPreprocessor(dpi=cfg.pdf.dpi)
        info = preprocessor.get_pdf_info(pdf_path)
        pages_to_process = info["page_count"]
        if cfg.pdf.max_pages:
            pages_to_process = min(cfg.pdf.max_pages, pages_to_process)

        progress.page_total = pages_to_process
        images = preprocessor.pdf_to_images(pdf_path, temp_dir, max_pages=cfg.pdf.max_pages)
        progress.preprocess_s = round(time.monotonic() - t0, 1)

        progress.phase = "ocr"
        client = OllamaClient(cfg.ollama)
        assembler = OutputAssembler(
            out_dir, source_filename=pdf_path.stem, debug=cfg.output.debug_mode
        )

        extracted: list[dict] = []
        total_s = 0.0
        n_req = 0

        for i, img in enumerate(images):
            progress.page_current = i + 1
            t_ocr = time.monotonic()

            try:
                text = client.ocr_image(img)
                ok = text and text.strip() and "[Unrecognized" not in text
                extracted.append(
                    {
                        "page": img.stem,
                        "type": "text" if ok else "unknown",
                        "content": text.strip() if text.strip() else "[Empty page]",
                    }
                )
                assembler.increment_pages()
                progress.pages_successful += 1
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

        progress.phase = "assembly"
        md = "\n\n".join(
            f"## {item['page']} ({item['type']})\n\n{item['content']}" for item in extracted
        )
        assembler.save_markdown(md, title=pdf_path.stem.replace("_", " ").title())

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
        progress.end_time = time.monotonic()
        if not cfg.output.debug_mode and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
        progress.phase = "done"
        processing = False


# ── Main page ─────────────────────────────────────────────
@ui.page("/")
def index():
    ui.add_head_html(CSS)

    theme_dark = ui.dark_mode()
    theme_dark.value = True

    async def resolve_theme():
        stored = await app.storage.user.get("theme", "auto")
        if stored == "auto":
            js_code = "window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'"
            detected = await ui.run_javascript(js_code)
            stored = detected if detected in ("dark", "light") else "dark"
        theme_dark.value = stored == "dark"
        ui.run_javascript(f"document.documentElement.setAttribute('data-theme', '{stored}')")

    asyncio.ensure_future(resolve_theme())

    async def toggle_theme():
        current = theme_dark.value
        new = not current
        theme_dark.value = new
        resolved = "dark" if new else "light"
        await app.storage.user.update({"theme": resolved})
        ui.run_javascript(f"document.documentElement.setAttribute('data-theme', '{resolved}')")

    # ── Header ──
    with ui.row().classes("w-full items-center justify-between px-4 py-3"):
        with ui.row().classes("items-center gap-3"):
            ui.html(
                '<span style="font-family:var(--font);font-size:22px;font-weight:700;'
                'color:var(--text-heading);letter-spacing:-0.01em">OCRSuite</span>'
            )
            ui.label("local document digitization").style(
                "color:var(--text-secondary);font-size:12px"
            )
        with ui.row().classes("items-center gap-3"):
            ui.button(icon="light_mode", on_click=toggle_theme).props("flat round dense")

    # ── System status bar ──
    with (
        ui.expansion("System Status")
        .props("dense")
        .classes("w-full mb-1")
        .style(
            "border:1px solid var(--border-light);border-radius:var(--radius-sm);overflow:hidden"
        )
    ):
        status_content = ui.row().classes("w-full gap-6 flex-wrap py-2")
        with status_content:
            ollama_stat = ui.html(
                '<div class="status-item">'
                '<span class="dot dot-off" style="width:8px;height:8px"></span>'
                '<span style="color:var(--text-secondary);font-size:12px">Ollama: checking…</span>'
                "</div>"
            )
            model_stat = ui.label("").style("color:var(--text-secondary);font-size:12px")
            disk_stat = ui.label("").style("color:var(--text-secondary);font-size:12px")
            ver_stat = ui.label("").style("color:var(--text-secondary);font-size:12px")

    async def update_status():
        healthy = await asyncio.to_thread(_ollama_healthy)
        models = await asyncio.to_thread(_ollama_models)
        version = await asyncio.to_thread(_ollama_version)
        disk = await asyncio.to_thread(_disk_usage_str)

        dot_color = "var(--success)" if healthy else "var(--error)"
        ollama_text = f"Ollama {version}" if healthy else "Ollama not detected"
        ollama_stat.content = (
            '<div class="status-item">'
            f'<span class="dot" style="width:8px;height:8px;background:{dot_color};animation:none"></span>'
            f'<span style="color:var(--text-secondary);font-size:12px">{ollama_text}</span>'
            "</div>"
        )
        model_stat.set_text(f"Models: {len(models)} installed")
        disk_stat.set_text(f"Disk: {disk}")
        ver_stat.set_text("OCRSuite v0.1.0")

        if healthy:
            process_btn.enable()
        else:
            process_btn.disable()

    # ═══════════════════════════════════════════════════════
    # 1 — UPLOAD
    # ═══════════════════════════════════════════════════════
    with ui.column().classes("w-full card-ocr p-4"):
        ui.label("Upload PDF").style(
            "color:var(--text-heading);font-size:14px;font-weight:600;margin-bottom:12px"
        )

        file_info = ui.label("Select a PDF file to begin").style(
            "color:var(--text-secondary);font-size:12px"
        )

        async def handle_upload(e):
            global uploaded_pdf
            try:
                path = Path(tempfile.gettempdir()) / f"ocrsuite_{e.file.name}"
                await e.file.save(str(path))
                uploaded_pdf = path
                size_mb = e.file.size() / (1024 * 1024)

                try:
                    from .preprocessor import PDFPreprocessor

                    pinfo = PDFPreprocessor().get_pdf_info(uploaded_pdf)
                    page_count = pinfo["page_count"]
                except Exception:
                    page_count = "?"

                file_info.set_text(f"{e.file.name}  —  {size_mb:.1f} MB · {page_count} pages")
                file_info.style("color:var(--success);font-size:13px")

                if not processing:
                    process_btn.enable()
            except Exception:
                ui.notify("Upload failed. Try again.", type="negative")

        ui.upload(
            on_upload=handle_upload,
            label="Choose PDF or drag here",
            auto_upload=True,
        ).props("accept=.pdf color=primary").classes("w-full")

    # ═══════════════════════════════════════════════════════
    # 2 — SETTINGS
    # ═══════════════════════════════════════════════════════
    with ui.column().classes("w-full card-ocr p-4 mt-3"):
        ui.label("Settings").style(
            "color:var(--text-heading);font-size:14px;font-weight:600;margin-bottom:12px"
        )

        models = _ollama_models()
        with ui.row().classes("w-full gap-4 items-end flex-wrap"):
            msel = (
                ui.select(
                    label="Model",
                    options=models,
                    value=models[0] if models else "ocrsuite-deepseek",
                )
                .classes("w-56")
                .props("outlined dense color=primary")
            )

            dpi = (
                ui.select(
                    label="DPI",
                    options={150: 150, 300: 300, 600: 600, 1200: 1200},
                    value=300,
                )
                .classes("w-28")
                .props("outlined dense color=primary")
            )

            mpages = (
                ui.select(
                    label="Max Pages",
                    options={"All": None, 5: 5, 10: 10, 20: 20, 50: 50, 100: 100},
                    value=None,
                )
                .classes("w-32")
                .props("outlined dense color=primary")
            )

            debug_cb = ui.checkbox("Debug", value=False).props("dense color=primary")

        with ui.expansion("Advanced").props("dense color=primary").classes("w-full mt-2"):
            post_cb = ui.checkbox("Post-process with vision model", value=False).props(
                "color=primary"
            )
            ui.label("Enrich OCR output: tables, links, ASCII art from figures").style(
                "color:var(--text-secondary);font-size:11px;margin-left:24px"
            )
            post_model = (
                ui.select(
                    label="Vision model",
                    options=[
                        m
                        for m in models
                        if any(v in m.lower() for v in ("llava", "vision", "bakllava", "granite"))
                    ]
                    or ["llava:13b"],
                    value="llava:13b",
                )
                .classes("w-56")
                .props("outlined dense color=primary")
            )

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

        session_dir = OUTPUT_ROOT / datetime.now().strftime("%d%m%y_%H%M%S")
        session_dir.mkdir(parents=True, exist_ok=True)
        progress.log_path = session_dir / "log.txt"
        progress.summary_shown = False

        process_btn.disable()
        process_btn.set_text("Processing…")
        await asyncio.to_thread(run_pipeline, uploaded_pdf, cfg, session_dir)
        process_btn.set_text("Process Another")
        process_btn.enable()

    process_btn = ui.button("Process Document", on_click=lambda: asyncio.ensure_future(start()))
    process_btn.props('color="primary" size="md"')
    process_btn.classes("w-full mt-4 font-semibold")
    process_btn.disable()

    asyncio.ensure_future(update_status())

    # ═══════════════════════════════════════════════════════
    # 4 — PIPELINE STATUS
    # ═══════════════════════════════════════════════════════
    with ui.column().classes("w-full card-ocr p-4 mt-3"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Pipeline Status").style(
                "color:var(--text-heading);font-size:14px;font-weight:600"
            )

        pre_row = ui.html(
            '<div class="phase-row"><span class="dot dot-off"></span>'
            '<span style="color:var(--text-secondary);font-size:13px">Preprocessing</span></div>'
        )
        ocr_row = ui.html(
            '<div class="phase-row"><span class="dot dot-off"></span>'
            '<span style="color:var(--text-secondary);font-size:13px">OCR Extraction</span></div>'
        )
        asm_row = ui.html(
            '<div class="phase-row"><span class="dot dot-off"></span>'
            '<span style="color:var(--text-secondary);font-size:13px">Assembly</span></div>'
        )
        pp_row = ui.html(
            '<div class="phase-row"><span class="dot dot-off"></span>'
            '<span style="color:var(--text-secondary);font-size:13px">Post-processing</span></div>'
        )

        page_prog = ui.linear_progress(0).props("rounded color=primary").classes("w-full mt-3")
        page_lbl = ui.label("").style("color:var(--text-secondary);font-size:11px;margin-top:4px")

        ollama_prog = ui.linear_progress(0).props("rounded color=info").classes("w-full mt-3")
        ollama_lbl = ui.label("").style("color:var(--text-secondary);font-size:11px;margin-top:4px")

    # ═══════════════════════════════════════════════════════
    # 5 — LOG VIEWER (inline)
    # ═══════════════════════════════════════════════════════
    log_expansion = (
        ui.expansion("View Log")
        .props("dense")
        .classes("w-full mt-2 hidden")
        .style(
            "border:1px solid var(--border-light);border-radius:var(--radius-sm);overflow:hidden"
        )
    )
    with log_expansion:
        log_content = ui.html('<div class="log-viewer">No log available yet.</div>')

    # ═══════════════════════════════════════════════════════
    # 6 — OUTPUT
    # ═══════════════════════════════════════════════════════
    out_card = ui.column().classes("w-full card-ocr p-4 mt-3")
    with out_card:
        out_header = ui.row().classes("w-full items-center justify-between mb-3")
        with out_header:
            ui.label("Output").style("color:var(--text-heading);font-size:14px;font-weight:600")
        out_body = ui.column().classes("w-full gap-0")

    with out_body:
        ui.html(
            '<div class="empty-state">'
            '<div style="color:var(--text-secondary);font-size:13px;margin-bottom:4px">'
            "Ready to process</div>"
            '<div style="color:var(--text-secondary);font-size:11px;line-height:1.5">'
            "Upload a PDF, configure settings, and press Process Document.<br>"
            "The pipeline runs entirely on your machine — no cloud, no API keys.</div>"
            '<div class="empty-steps">'
            '<div class="empty-step">'
            '<div class="empty-step-icon" style="background:var(--surface-alt);color:var(--primary)">1</div>'
            '<span style="color:var(--text-secondary);font-size:11px">Upload PDF</span>'
            "</div>"
            '<div class="empty-step">'
            '<div class="empty-step-icon" style="background:var(--surface-alt);color:var(--info)">2</div>'
            '<span style="color:var(--text-secondary);font-size:11px">Configure</span>'
            "</div>"
            '<div class="empty-step">'
            '<div class="empty-step-icon" style="background:var(--surface-alt);color:var(--success)">3</div>'
            '<span style="color:var(--text-secondary);font-size:11px">Process</span>'
            "</div>"
            "</div>"
            "</div>"
        )

    # ═══════════════════════════════════════════════════════
    # 7 — SESSION HISTORY
    # ═══════════════════════════════════════════════════════
    hist_expansion = (
        ui.expansion("Session History")
        .props("dense")
        .classes("w-full mt-3")
        .style(
            "border:1px solid var(--border-light);border-radius:var(--radius-sm);overflow:hidden"
        )
    )
    with hist_expansion:
        hist_container = ui.column().classes("w-full gap-1 py-2")
        with hist_container:
            ui.label("Loading history…").style("color:var(--text-secondary);font-size:12px")

    async def load_history():
        sessions = await asyncio.to_thread(_scan_sessions)
        hist_container.clear()
        with hist_container:
            if not sessions:
                ui.label("No previous sessions found.").style(
                    "color:var(--text-secondary);font-size:12px"
                )
            for s in sessions[:20]:
                ts_str = s["timestamp"].strftime("%d %b %Y, %H:%M")
                with (
                    ui.row()
                    .classes("w-full")
                    .style(
                        "padding:10px 12px;border:1px solid var(--border-light);"
                        "border-radius:var(--radius-sm);margin-bottom:6px;"
                        "transition:all var(--transition)"
                    )
                ):
                    with ui.column().classes("gap-1"):
                        ui.label(ts_str).style(
                            "color:var(--text-primary);font-size:13px;font-weight:600"
                        )
                        ui.label(f"{s['file_count']} files · {s['total_kb']} KB").style(
                            "color:var(--text-secondary);font-size:11px"
                        )
                    ui.space()
                    if session_dir and str(s["path"]) == str(session_dir):
                        ui.html(
                            '<span style="background:var(--success);color:var(--primary-text);'
                            "padding:2px 8px;border-radius:var(--radius-sm);font-size:10px;"
                            'font-weight:600">current</span>'
                        )

    asyncio.ensure_future(load_history())

    # ── Phase update helper ──
    def _phase_html(name: str, label: str, current_idx: int) -> str:
        idx = {"preprocessing": 1, "ocr": 2, "assembly": 3, "postprocess": 4}.get(name, 0)
        color = "var(--text-secondary)"
        dot_cls = "dot-off"
        text = label

        if name == "preprocessing" and progress.preprocess_s > 0:
            text = f"Preprocessing — {progress.preprocess_s}s"

        if current_idx == 5:
            dot_cls = "dot-done"
            color = "var(--success)"
        elif current_idx > idx:
            dot_cls = "dot-done"
            color = "var(--success)"
        elif current_idx == idx:
            dot_cls = "dot-on"
            color = "var(--primary)"

        return (
            '<div class="phase-row">'
            f'<span class="dot {dot_cls}"></span>'
            f'<span style="color:{color};font-size:13px">{text}</span>'
            "</div>"
        )

    # ═══════════════════════════════════════════════════════
    # POLLING (300ms)
    # ═══════════════════════════════════════════════════════
    def poll():
        phase_map = {
            "idle": 0,
            "preprocessing": 1,
            "ocr": 2,
            "assembly": 3,
            "postprocess": 4,
            "done": 5,
        }
        current = phase_map.get(progress.phase, 0)

        pre_row.content = _phase_html("preprocessing", "Preprocessing", current)
        ocr_row.content = _phase_html("ocr", "OCR Extraction", current)
        asm_row.content = _phase_html("assembly", "Assembly", current)
        pp_row.content = _phase_html("postprocess", "Post-processing", current)

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

        # ── Ollama per-page ──
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

        # ── Log viewer visibility ──
        if current in (1, 2, 3, 4):
            log_expansion.classes(remove="hidden")
            if progress.log_path and progress.log_path.exists():
                try:
                    log_text = progress.log_path.read_text(encoding="utf-8", errors="replace")
                    log_content.content = f'<div class="log-viewer">{log_text[-8000:]}</div>'
                except Exception:
                    pass
        else:
            log_expansion.classes(add="hidden")

        # ── Output / Summary ──
        if progress.phase == "done" and not progress.summary_shown:
            progress.summary_shown = True
            total_s = progress.end_time - progress.start_time if progress.end_time > 0 else 0
            m, s = int(total_s // 60), int(total_s % 60)

            total_out_kb = sum(f["size_kb"] for f in progress.output_files)

            out_body.clear()
            with out_body:
                # Summary
                ui.html(
                    '<div class="summary-grid">'
                    f'<div class="summary-item">'
                    f'<div class="summary-value" style="color:var(--primary)">{m}m {s}s</div>'
                    f'<div style="color:var(--text-secondary);font-size:11px;margin-top:4px">Duration</div>'
                    f"</div>"
                    f'<div class="summary-item">'
                    f'<div class="summary-value" style="color:var(--info)">{progress.pages_done}/{progress.page_total}</div>'
                    f'<div style="color:var(--text-secondary);font-size:11px;margin-top:4px">Pages</div>'
                    f"</div>"
                    f'<div class="summary-item">'
                    f'<div class="summary-value" style="color:var(--success)">{len(progress.output_files)}</div>'
                    f'<div style="color:var(--text-secondary);font-size:11px;margin-top:4px">Files</div>'
                    f"</div>"
                    f'<div class="summary-item">'
                    f'<div class="summary-value" style="color:var(--text-secondary)">{total_out_kb:.0f} KB</div>'
                    f'<div style="color:var(--text-secondary);font-size:11px;margin-top:4px">Output</div>'
                    f"</div>"
                    "</div>"
                )

                if progress.errors and not progress.output_files:
                    ui.label("Processing failed with errors:").style(
                        "color:var(--error);font-size:13px;margin-top:16px;margin-bottom:8px"
                    )
                    for e in progress.errors:
                        ui.label(f"  {e}").style("color:var(--text-secondary);font-size:11px")

                # Output files
                if progress.output_files:
                    ui.html(
                        '<div style="color:var(--text-heading);font-size:13px;font-weight:600;'
                        'margin-top:20px;margin-bottom:8px">Output Files</div>'
                    )
                    for f in progress.output_files:
                        fpath = str(session_dir / f["name"]) if session_dir else ""
                        with ui.row().classes("file-row w-full"):
                            ui.label(f"{f['name']}  ({f['size_kb']} KB)").style(
                                "color:var(--text-primary);font-size:13px"
                            )
                            dl = ui.button("Download", on_click=lambda p=fpath: ui.download(p))
                            dl.props("flat size=sm color=primary dense")

                # Reload session history
                asyncio.ensure_future(load_history())

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
        storage_secret="ocrsuite-local",
        native=native,
        reload=False,
        show=False if native else True,
    )
