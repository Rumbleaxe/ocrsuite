"""Main CLI entry point for OCRSuite."""

import shutil
from pathlib import Path
from typing import Optional

import typer
from loguru import logger
from rich.console import Console
from rich.progress import Progress

from . import __version__
from .assembler import OutputAssembler
from .config import Config
from .ollama_client import OllamaClient
from .postprocessor import PostProcessor
from .preprocessor import PDFPreprocessor
from .utils import OCRSuiteError, init_logging

app = typer.Typer(
    name="ocrsuite",
    help="AI-powered PDF processing for digitizing old books.",
    no_args_is_help=True,
)

console = Console()


@app.command()
def process(
    input: Path = typer.Option(
        ...,
        "--input",
        help="Path to input PDF file.",
        exists=True,
        dir_okay=False,
    ),
    output: Path = typer.Option(
        "./output",
        "--output",
        help="Output directory for extracted content.",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        help="Path to configuration YAML file.",
        exists=True,
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        help="Ollama model to use (default: ocrsuite-deepseek). Check available with: ollama list. For custom models, see docs/MODELFILE.md",
    ),
    max_pages: Optional[int] = typer.Option(
        None,
        "--max-pages",
        help="Maximum number of pages to process.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging.",
    ),
    postprocess: bool = typer.Option(
        False,
        "--postprocess",
        help="Post-process with vision model (tables, links, ASCII art).",
    ),
    postprocess_model: Optional[str] = typer.Option(
        None,
        "--postprocess-model",
        help="Vision model for enrichment (default: llava:13b).",
    ),
) -> None:
    """Process a PDF file and extract text, tables, and figures.

    This command will:
    1. Convert PDF pages to high-resolution images
    2. Send to Ollama for OCR and content classification
    3. Extract and convert content to LaTeX, PNG, and Markdown formats
    4. Optionally post-process with a vision model for enriched output
    5. Save results to the output directory
    """
    output_path = Path(output)
    init_logging(output_path, verbose)
    logger.info(f"Processing PDF: {input}")
    logger.info(f"Output directory: {output_path}")

    if postprocess_model:
        logger.info(f"Post-processing model override: {postprocess_model}")

    try:
        with Progress(console=console) as progress:
            # Load configuration
            task_config = progress.add_task("[cyan]Loading configuration...", total=None)
            if config:
                cfg = Config.from_file(config)
                logger.info(f"Configuration loaded from: {config}")
            else:
                cfg = Config()
                logger.info("Using default configuration")

            if model:
                cfg.ollama.model = model
                logger.info(f"Model override: {model}")
            if max_pages:
                cfg.pdf.max_pages = max_pages
                logger.info(f"Max pages limit: {max_pages}")
            if postprocess:
                cfg.postprocess.enabled = True
            if postprocess_model:
                cfg.postprocess.model = postprocess_model

            progress.update(task_config, completed=True)
            logger.info(
                f"Configuration ready: model={cfg.ollama.model}, dpi={cfg.pdf.dpi}, timeout={cfg.ollama.timeout}s"
            )
            console.print(f"[green]✓[/green] Configuration loaded (model: {cfg.ollama.model})")

            # Check Ollama health
            task_ollama = progress.add_task("[cyan]Checking Ollama connection...", total=None)
            client = OllamaClient(cfg.ollama)
            logger.info(f"Connecting to Ollama at {cfg.ollama.url}...")
            if not client.health_check():
                progress.update(task_ollama, visible=False)
                logger.error(f"Cannot connect to Ollama at {cfg.ollama.url}")
                console.print(
                    "[red]✗ Ollama not running![/red]\n"
                    "Start it with: [bold]ollama serve[/bold]\n"
                    "Then pull a model: [bold]ollama pull llama2-vision[/bold]"
                )
                raise OCRSuiteError(f"Could not connect to Ollama at {cfg.ollama.url}")

            progress.update(task_ollama, completed=True)
            logger.info(f"✓ Connected to Ollama at {cfg.ollama.url}")
            console.print(f"[green]✓[/green] Connected to Ollama at {cfg.ollama.url}")

            # Preprocess PDF
            task_preprocess = progress.add_task("[cyan]Converting PDF to images...", total=None)
            preprocessor = PDFPreprocessor(dpi=cfg.pdf.dpi)
            logger.info(f"Reading PDF: {input}")
            pdf_info = preprocessor.get_pdf_info(input)
            logger.info(f"PDF info: {pdf_info['page_count']} pages")
            console.print(f"[bold]PDF Info:[/bold] {pdf_info['page_count']} pages")

            temp_images_dir = Path(output) / ".temp_images"
            image_paths = preprocessor.pdf_to_images(
                input, temp_images_dir, max_pages=cfg.pdf.max_pages
            )
            progress.update(task_preprocess, completed=True)
            console.print(f"[green]✓[/green] Converted {len(image_paths)} pages to images")

            # Initialize output
            assembler = OutputAssembler(
                Path(output), source_filename=input.stem, debug=cfg.output.debug_mode
            )

            # Process each image with Ollama
            task_ocr = progress.add_task(
                "[cyan]Extracting content with Ollama...",
                total=len(image_paths),
            )

            extracted_content = []
            for image_path in image_paths:
                try:
                    # Always attempt direct OCR extraction
                    # Classification doesn't work reliably with DeepSeek-OCR
                    text = client.ocr_image(image_path)

                    # Try to detect if response is actually meaningful
                    # (vs placeholder text)
                    if text and text.strip() and "[Unrecognized" not in text:
                        content_type = "text"
                    else:
                        content_type = "unknown"
                        logger.debug(f"Page {image_path.stem}: empty or placeholder OCR response")

                    extracted_content.append(
                        {
                            "page": image_path.stem,
                            "type": content_type,
                            "content": text
                            if text.strip()
                            else "[Empty page or unrecognized content]",
                        }
                    )

                    assembler.increment_pages()

                except Exception as e:
                    console.print(f"[yellow]⚠ Error processing {image_path.name}: {e}[/yellow]")
                    logger.error(f"Error processing {image_path.name}: {e}", exc_info=verbose)
                    assembler.record_error(f"{image_path.name}: {e}")

                finally:
                    progress.update(task_ocr, advance=1)

            pages_processed = assembler.metadata["pages_processed"]
            errors_count = len(assembler.metadata["errors"])
            logger.info(
                f"✓ Extraction complete: {pages_processed} pages processed, {errors_count} errors"
            )
            console.print(f"[green]✓[/green] Extracted content from {pages_processed} pages")

            # Assemble single markdown output with linked figures
            logger.info("Assembling markdown output with linked figures...")
            md_content = "\n\n".join(
                f"## {item['page']} ({item['type']})\n\n{item['content']}"
                for item in extracted_content
            )

            output_file = assembler.save_markdown(
                md_content,
                title=input.stem.replace("_", " ").title(),
            )
            logger.info(f"✓ Markdown document saved: {output_file.name}")

            # Post-processing (optional)
            if cfg.postprocess.enabled:
                from .config import OllamaConfig

                logger.info("Post-processing with vision model...")
                task_pp = progress.add_task(
                    "[cyan]Post-processing with vision model...", total=None
                )

                pp_client = OllamaClient(
                    OllamaConfig(
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
                enriched = processor.postprocess(output_file, figures_dir or output_path)

                pp_path = output_path / f"postprocessed_{output_file.name}"
                pp_path.write_text(enriched, encoding="utf-8")
                progress.update(task_pp, completed=True)
                console.print(f"[green]✓[/green] Post-processed: {pp_path.name}")
                logger.info(f"✓ Post-processed document saved: {pp_path.name}")

            # Cleanup temp images if not debug mode
            if not cfg.output.debug_mode and temp_images_dir.exists():
                shutil.rmtree(temp_images_dir, ignore_errors=True)

            # Success summary
            logger.info("OCRSuite processing completed successfully!")
            console.print("\n[bold green]✓ Processing Complete![/bold green]\n")
            console.print(f"[bold]Output Directory:[/bold] {Path(output).resolve()}")
            console.print("[bold]Output File:[/bold]")
            console.print(f"  - {output_file.name}")
            figures_found = (
                len(list((assembler.figures_dir or Path("/dev/null")).glob("figure_*.png")))
                if assembler.figures_dir
                else 0
            )
            if figures_found > 0:
                console.print(f"  - {assembler.get_figures_dirname()}/ ({figures_found} figures)")

    except OCRSuiteError as e:
        logger.error(f"OCRSuite error: {e}", exc_info=verbose)
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from e
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        console.print(f"[red]Unexpected error:[/red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1) from e
    finally:
        logger.info("OCRSuite process finished.")


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"[bold]OCRSuite[/bold] v{__version__}")


if __name__ == "__main__":
    app()
