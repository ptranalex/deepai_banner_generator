#!/usr/bin/env python3
"""DeepAI Banner Generator - Main CLI

Modern AI-powered banner generator for blog posts using Typer CLI framework.
"""

from enum import Enum
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from lib.config import get_settings
from lib.deepai import DeepAIClient
from lib.file_handler import MarkdownHandler, OutputHandler
from lib.gpt import GPTClient
from lib.selection_parser import parse_selection

app = typer.Typer(
    name="deepai-banner",
    help="Generate AI-powered banner images from blog posts",
    add_completion=False,
)
console = Console()


class Style(str, Enum):
    """Prompt generation style options"""

    simple = "simple"
    origami = "origami"


class Version(str, Enum):
    """DeepAI generator version options"""

    standard = "standard"
    hd = "hd"
    genius = "genius"


def interactive_select_file(files: list[Path]) -> Path:
    """Display files and let user select one interactively

    Args:
        files: List of file paths to choose from

    Returns:
        Selected file path
    """
    if not files:
        console.print("[red]No markdown files found.[/red]")
        raise typer.Exit(1)

    # Create a table for file selection
    table = Table(title="📁 Available Markdown Files", show_header=True)
    table.add_column("#", style="cyan", width=4)
    table.add_column("File", style="green")

    for idx, file_path in enumerate(files, 1):
        display_name = file_path.name if len(str(file_path)) > 50 else str(file_path)
        table.add_row(str(idx), display_name)

    console.print(table)

    while True:
        try:
            choice = console.input(
                f"\n[bold cyan]Select a file (1-{len(files)}) or 'q' to quit:[/bold cyan] "
            ).strip()

            if choice.lower() == "q":
                console.print("[yellow]Exiting...[/yellow]")
                raise typer.Exit(0)

            choice_num = int(choice)
            if 1 <= choice_num <= len(files):
                return files[choice_num - 1]
            else:
                console.print(
                    f"[red]Please enter a number between 1 and {len(files)}[/red]"
                )
        except ValueError:
            console.print(
                "[red]Invalid input. Please enter a number or 'q' to quit.[/red]"
            )
        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting...[/yellow]")
            raise typer.Exit(0) from None


def interactive_select_prompt(prompts: list[str]) -> str:
    """Display prompts and let user select one interactively

    Args:
        prompts: List of prompt strings

    Returns:
        Selected prompt
    """
    table = Table(
        title=f"💡 Generated {len(prompts)} Origami Prompts", show_header=True
    )
    table.add_column("#", style="cyan", width=4)
    table.add_column("Prompt", style="magenta")

    for idx, prompt in enumerate(prompts, 1):
        table.add_row(str(idx), prompt)

    console.print(table)

    while True:
        try:
            choice = console.input(
                f"\n[bold cyan]Select a prompt (1-{len(prompts)}) or 'q' to quit:[/bold cyan] "
            ).strip()

            if choice.lower() == "q":
                console.print("[yellow]Cancelled.[/yellow]")
                raise typer.Exit(0)

            choice_num = int(choice)
            if 1 <= choice_num <= len(prompts):
                return prompts[choice_num - 1]
            else:
                console.print(
                    f"[red]Please enter a number between 1 and {len(prompts)}[/red]"
                )
        except ValueError:
            console.print(
                "[red]Invalid input. Please enter a number or 'q' to quit.[/red]"
            )
        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting...[/yellow]")
            raise typer.Exit(0) from None


def interactive_select_prompts(prompts: list[str]) -> list[int]:
    """Display prompts and let user select multiple

    Args:
        prompts: List of prompt strings

    Returns:
        List of selected prompt indices (0-based)
    """
    table = Table(
        title=f"💡 Generated {len(prompts)} Origami Prompts", show_header=True
    )
    table.add_column("#", style="cyan", width=4)
    table.add_column("Prompt", style="magenta")

    for idx, prompt in enumerate(prompts, 1):
        table.add_row(str(idx), prompt)

    console.print(table)
    console.print("\n[bold cyan]Multi-Select Options:[/bold cyan]")
    console.print("  • Single: [dim]1[/dim]")
    console.print("  • Multiple: [dim]1,3,5[/dim] or [dim]1 3 5[/dim]")
    console.print("  • Range: [dim]1-5[/dim]")
    console.print("  • All: [dim]all[/dim]")
    console.print("  • Quit: [dim]q[/dim]")

    while True:
        try:
            choice = console.input("\n[bold cyan]Select prompts:[/bold cyan] ").strip()

            if choice.lower() == "q":
                console.print("[yellow]Cancelled.[/yellow]")
                raise typer.Exit(0)

            if choice.lower() == "all":
                selected = list(range(len(prompts)))
                console.print(f"\n[green]Selected all {len(selected)} prompts[/green]")
                return selected

            # Parse selection
            selected = parse_selection(choice, len(prompts))

            if selected:
                # Show confirmation
                console.print(
                    f"\n[green]Selected {len(selected)} prompt(s): "
                    f"{[i + 1 for i in selected]}[/green]"
                )
                return selected
            else:
                console.print("[red]Invalid selection. Try again.[/red]")

        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0) from None


@app.command()
def generate(
    input_dir: Path | None = typer.Option(
        None,
        "--input-dir",
        "-i",
        help="Directory containing markdown blog posts",
    ),
    output_dir: Path | None = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for generated banners",
    ),
    style: Style = typer.Option(
        Style.origami,
        "--style",
        "-s",
        help="Prompt generation style",
    ),
    width: int = typer.Option(
        1024,
        "--width",
        "-w",
        min=128,
        max=1536,
        help="Banner width (must be multiple of 32)",
    ),
    height: int = typer.Option(
        512,
        "--height",
        "-h",
        min=128,
        max=1536,
        help="Banner height (must be multiple of 32)",
    ),
    version: Version = typer.Option(
        Version.standard,
        "--version",
        "-v",
        help="DeepAI image generator version",
    ),
    openai_key: str | None = typer.Option(
        None,
        "--openai-key",
        envvar="OPENAI_API_KEY",
        help="OpenAI API key (or set OPENAI_API_KEY env var)",
    ),
    deepai_key: str | None = typer.Option(
        None,
        "--deepai-key",
        envvar="DEEPAI_API_KEY",
        help="DeepAI API key (or set DEEPAI_API_KEY env var)",
    ),
) -> None:
    """Generate banner image from blog post using AI"""

    # Load settings
    try:
        settings = get_settings()
        input_dir = input_dir or settings.default_input_dir
        output_dir = output_dir or settings.default_output_dir
    except Exception as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        console.print("\n[yellow]Set API keys via:[/yellow]")
        console.print("  1. Environment: export OPENAI_API_KEY='sk-...'")
        console.print("  2. .env file: Copy .env.example to .env and edit")
        console.print("  3. CLI flag: --openai-key 'sk-...'")
        raise typer.Exit(1) from e

    # Validate dimensions
    if width % 32 != 0 or height % 32 != 0:
        console.print("[red]Error: Width and height must be multiples of 32[/red]")
        raise typer.Exit(1)

    # Initialize clients
    try:
        gpt_client = GPTClient(openai_key)
        deepai_client = DeepAIClient(deepai_key)
    except Exception as e:
        console.print(f"[red]Failed to initialize clients: {e}[/red]")
        raise typer.Exit(1) from e

    # Find markdown files
    console.print(f"🔍 Searching for markdown files in: [cyan]{input_dir}[/cyan]")
    files = MarkdownHandler.find_markdown_files(input_dir)

    if not files:
        console.print(f"[red]No markdown files found in {input_dir}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Found {len(files)} markdown file(s)[/green]\n")

    # Interactive file selection
    selected_file = interactive_select_file(files)
    console.print(f"\n✅ [green]Selected:[/green] {selected_file}")

    # Parse the file
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("📖 Parsing blog post...", total=None)
        front_matter, body = MarkdownHandler.parse_markdown_post(selected_file)
        progress.update(task, completed=True)

    # Get title and display info
    title = front_matter.get("title", "Blog Post")
    tags = front_matter.get("tags", []) + front_matter.get("categories", [])

    info_panel = Panel(
        f"[bold]Title:[/bold] {title}\n"
        f"[bold]Tags:[/bold] {', '.join(tags[:5]) if tags else 'None'}\n"
        f"[bold]Style:[/bold] {style.value}",
        title="📄 Post Info",
        border_style="blue",
    )
    console.print(info_panel)

    # Generate prompts based on style
    banner_prompts: list[str] = []

    if style == Style.origami:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                "🤖 Asking ChatGPT to create 10 origami-style prompts...", total=None
            )
            prompts = gpt_client.generate_origami_prompts(title, body)
            progress.update(task, completed=True)

        if not prompts:
            console.print("[red]❌ No prompts generated. Exiting.[/red]")
            raise typer.Exit(1)

        # Always use multi-select (users can select just one by entering "1")
        selected_indices = interactive_select_prompts(prompts)
        banner_prompts = [prompts[i] for i in selected_indices]

    else:  # simple style
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                "🤖 Asking ChatGPT to create a banner prompt...", total=None
            )
            banner_prompt = gpt_client.generate_simple_prompt(title, body)
            progress.update(task, completed=True)

        console.print(
            Panel(
                f'[magenta]"{banner_prompt}"[/magenta]',
                title="💡 Generated Prompt",
                border_style="magenta",
            )
        )

        # Confirm before generating
        proceed = (
            console.input(
                "\n[bold cyan]Generate banner with this prompt? (Y/n):[/bold cyan] "
            )
            .strip()
            .lower()
        )
        if proceed and proceed != "y":
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)

    # Prepare output path(s) - always use batch mode logic
    output_dir.mkdir(parents=True, exist_ok=True)

    if banner_prompts:
        # Generate using batch logic (handles single or multiple)
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_paths = OutputHandler.generate_batch_output_paths(
            selected_file, output_dir, len(banner_prompts), timestamp
        )

        # Ensure directories exist
        for output_path in output_paths:
            OutputHandler.ensure_output_directory(output_path)

        # Show appropriate message
        if len(banner_prompts) == 1:
            console.print("\n🎨 [bold]Generating banner via DeepAI...[/bold]")
        else:
            console.print(
                f"\n🎨 [bold]Generating {len(banner_prompts)} banners...[/bold]"
            )

        # Generate all banners with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating banners...", total=len(banner_prompts))

            successful = 0
            failed = 0

            for prompt, output_path in zip(banner_prompts, output_paths, strict=False):
                progress.update(task, description=f"Generating {output_path.name}...")

                success = deepai_client.generate_and_save(
                    prompt=prompt,
                    output_path=output_path,
                    width=width,
                    height=height,
                    version=version.value,
                )

                if success:
                    console.print(f"  ✓ [green]{output_path.name}[/green]")
                    successful += 1
                else:
                    console.print(f"  ✗ [red]{output_path.name}[/red]")
                    failed += 1

                progress.advance(task)

        # Summary
        if len(banner_prompts) == 1:
            if successful:
                console.print(
                    f"\n✨ [bold green]Done![/bold green] Banner saved to: [cyan]{output_paths[0]}[/cyan]"
                )
            else:
                console.print("\n[red]❌ Banner generation failed.[/red]")
                raise typer.Exit(1)
        else:
            console.print(
                f"\n✨ [bold green]Batch complete![/bold green] "
                f"✓ {successful} successful, ✗ {failed} failed"
            )
            console.print(f"[cyan]Output directory: {output_dir}[/cyan]")


@app.command()
def direct(
    prompt: str = typer.Argument(..., help="Banner image prompt"),
    output: Path = typer.Option(
        Path("banner.png"),
        "--output",
        "-o",
        help="Output file path",
    ),
    width: int = typer.Option(
        1024,
        "--width",
        "-w",
        min=128,
        max=1536,
        help="Banner width (must be multiple of 32)",
    ),
    height: int = typer.Option(
        512,
        "--height",
        "-h",
        min=128,
        max=1536,
        help="Banner height (must be multiple of 32)",
    ),
    version: Version = typer.Option(
        Version.standard,
        "--version",
        "-v",
        help="DeepAI image generator version",
    ),
    deepai_key: str | None = typer.Option(
        None,
        "--deepai-key",
        envvar="DEEPAI_API_KEY",
        help="DeepAI API key",
    ),
) -> None:
    """Generate banner directly from a text prompt (no AI chain)"""

    # Validate dimensions
    if width % 32 != 0 or height % 32 != 0:
        console.print("[red]Error: Width and height must be multiples of 32[/red]")
        raise typer.Exit(1)

    # Initialize DeepAI client
    try:
        deepai_client = DeepAIClient(deepai_key)
    except Exception as e:
        console.print(f"[red]Failed to initialize DeepAI client: {e}[/red]")
        console.print(
            "\n[yellow]Set DEEPAI_API_KEY environment variable or use --deepai-key[/yellow]"
        )
        raise typer.Exit(1) from e

    # Prepare output
    OutputHandler.ensure_output_directory(output)

    # Display info
    console.print(
        Panel(
            f"[bold]Prompt:[/bold] {prompt}\n"
            f"[bold]Dimensions:[/bold] {width}x{height}\n"
            f"[bold]Version:[/bold] {version.value}\n"
            f"[bold]Output:[/bold] {output}",
            title="🎨 Generation Info",
            border_style="cyan",
        )
    )

    # Generate
    console.print("\n🎨 [bold]Generating banner...[/bold]")

    success = deepai_client.generate_and_save(
        prompt=prompt,
        output_path=output,
        width=width,
        height=height,
        version=version.value,
    )

    if success:
        console.print(
            f"\n✨ [bold green]Done![/bold green] Banner saved to: [cyan]{output}[/cyan]"
        )
    else:
        console.print("\n[red]❌ Banner generation failed.[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
