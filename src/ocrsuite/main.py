"""Main CLI entry point for OCRSuite."""

import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress

from . import __version__
from .assembler import OutputAssembler
from .config import Config
from .ollama_client import OllamaClient
from .preprocessor import PDFPreprocessor
from .utils import setup_logging, OCRSuiteError

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
        help="Ollama model to use (e.g., llama2-vision).",
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
) -> None:
    """Process a PDF file and extract text, tables, and figures.

    This command will:
    1. Convert PDF pages to high-resolution images
    2. Send to Ollama for OCR and content classification
    3. Extract and convert content to LaTeX, PNG, and Markdown formats
    4. Save results to the output directory
    """
    setup_logging(verbose)

    try:
        with Progress(console=console) as progress:
            # Load configuration
            task_config = progress.add_task(
                "[cyan]Loading configuration...", total=None
            )
            if config:
                cfg = Config.from_file(config)
            else:
                cfg = Config()

            if model:
                cfg.ollama.model = model
            if max_pages:
                cfg.pdf.max_pages = max_pages

            progress.update(task_config, completed=True)
            console.print(
                f"[green]✓[/green] Configuration loaded "
                f"(model: {cfg.ollama.model})"
            )

            # Check Ollama health
            task_ollama = progress.add_task(
                "[cyan]Checking Ollama connection...", total=None
            )
            client = OllamaClient(cfg.ollama)
            if not client.health_check():
                progress.update(task_ollama, visible=False)
                console.print(
                    "[red]✗ Ollama not running![/red]\n"
                    "Start it with: [bold]ollama serve[/bold]\n"
                    "Then pull a model: [bold]ollama pull llama2-vision[/bold]"
                )
                raise OCRSuiteError(
                    f"Could not connect to Ollama at {cfg.ollama.url}"
                )

            progress.update(task_ollama, completed=True)
            console.print(
                f"[green]✓[/green] Connected to Ollama at {cfg.ollama.url}"
            )

            # Preprocess PDF
            task_preprocess = progress.add_task(
                "[cyan]Converting PDF to images...", total=None
            )
            preprocessor = PDFPreprocessor(dpi=cfg.pdf.dpi)
            pdf_info = preprocessor.get_pdf_info(input)
            console.print(
                f"[bold]PDF Info:[/bold] {pdf_info['page_count']} pages"
            )

            temp_images_dir = Path(output) / ".temp_images"
            image_paths = preprocessor.pdf_to_images(
                input, temp_images_dir, max_pages=cfg.pdf.max_pages
            )
            progress.update(task_preprocess, completed=True)
            console.print(
                f"[green]✓[/green] Converted {len(image_paths)} pages to images"
            )

            # Initialize output
            assembler = OutputAssembler(Path(output), debug=cfg.output.debug_mode)

            # Process each image with Ollama
            task_ocr = progress.add_task(
                "[cyan]Extracting content with Ollama...",
                total=len(image_paths),
            )

            extracted_content = []
            for image_path in image_paths:
                try:
                    # Classify content
                    classification = client.classify_content(image_path)

                    # Extract based on type
                    if classification["type"] in ("text", "mixed"):
                        text = client.ocr_image(image_path)
                    elif classification["type"] == "table":
                        text = client.extract_table(image_path)
                    elif classification["type"] == "figure":
                        # Save figure directly
                        figure_num = len(
                            [
                                p
                                for p in Path(output).glob("figure_*.png")
                                if p.is_file()
                            ]
                        ) + 1
                        assembler.save_image(
                            image_path, f"figure_{figure_num:03d}.png"
                        )
                        text = f"[Figure {figure_num} - see figure_{figure_num:03d}.png]"
                    else:
                        text = "[Unrecognized content]"

                    extracted_content.append(
                        {
                            "page": image_path.stem,
                            "type": classification["type"],
                            "content": text,
                        }
                    )

                    assembler.increment_pages()

                except Exception as e:
                    console.print(
                        f"[yellow]⚠ Error processing {image_path.name}: {e}[/yellow]"
                    )
                    assembler.record_error(f"{image_path.name}: {e}")

                finally:
                    progress.update(task_ocr, advance=1)

            console.print(
                f"[green]✓[/green] Extracted content from {assembler.metadata['pages_processed']} pages"
            )

            # Assemble outputs
            if cfg.output.format_latex:
                latex_content = "\n\n".join(
                    f"% {item['page']} ({item['type']})\n{item['content']}"
                    for item in extracted_content
                )
                assembler.save_latex(
                    latex_content,
                    filename="document.tex",
                    title=input.stem.replace("_", " ").title(),
                )

            if cfg.output.format_markdown:
                md_content = "\n\n".join(
                    f"## {item['page']} ({item['type']})\n\n{item['content']}"
                    for item in extracted_content
                )
                assembler.save_markdown(md_content, filename="extraction.md")

            assembler.save_metadata()

            # Success summary
            console.print("\n[bold green]✓ Processing Complete![/bold green]\n")
            console.print(f"[bold]Output Directory:[/bold] {Path(output).resolve()}")
            console.print(f"[bold]Files Generated:[/bold]")
            console.print(f"  - document.tex (LaTeX)")
            console.print(f"  - extraction.md (Markdown)")
            console.print(
                f"  - figure_*.png ({len(list(Path(output).glob('figure_*.png')))} figures)"
            )
            console.print(f"  - metadata.txt")

            # Cleanup temp images if not debug mode
            if not cfg.output.debug_mode and temp_images_dir.exists():
                import shutil

                shutil.rmtree(temp_images_dir, ignore_errors=True)

    except OCRSuiteError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from e
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1) from e


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"[bold]OCRSuite[/bold] v{__version__}")


if __name__ == "__main__":
    app()
