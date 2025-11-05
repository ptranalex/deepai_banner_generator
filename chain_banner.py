#!/usr/bin/env python3
"""DeepAI Banner Generator - Main CLI

Modern AI-powered banner generator for blog posts using Typer CLI framework.
"""

import asyncio
from enum import Enum
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from lib.config import get_settings
from lib.deepai import DeepAIClient, get_style_loader
from lib.file_handler import MarkdownHandler, OutputHandler
from lib.gpt import GPTClient
from lib.selection_parser import parse_selection

app = typer.Typer(
    name="deepai-banner",
    help="Generate AI-powered banner images from blog posts",
    add_completion=False,
)
console = Console()


class Version(str, Enum):
    """DeepAI generator version options"""

    standard = "standard"
    hd = "hd"
    genius = "genius"


def interactive_select_style(
    default_slug: str = "origami-3d-generator",
    suggestions: list[tuple[str, float, str]] | None = None,
) -> str:
    """Display styles and let user select one interactively

    Args:
        default_slug: Default style slug to pre-select
        suggestions: Optional list of (slug, confidence, reasoning) tuples from GPT

    Returns:
        Selected style slug
    """
    loader = get_style_loader()
    styles = loader.list_styles()

    if not styles:
        console.print("[red]No styles found in configuration.[/red]")
        raise typer.Exit(1)

    # If suggestions provided, show them in a panel first
    if suggestions:
        console.print("\n💡 [bold cyan]AI Style Recommendations:[/bold cyan]\n")

        for rank, (slug, confidence, reasoning) in enumerate(suggestions, 1):
            style_obj = loader.get_style(slug)
            if style_obj:
                confidence_pct = int(confidence * 100)
                console.print(
                    f"  {rank}. [bold green]{style_obj.name}[/bold green] "
                    f"[dim]({confidence_pct}% match)[/dim]"
                )
                console.print(f"     [dim]{reasoning}[/dim]\n")

    # Create suggestion lookup for highlighting
    suggestion_slugs = {
        slug: (confidence, rank) for rank, (slug, confidence, _) in enumerate(suggestions or [], 1)
    }

    # Find default index (prefer top suggestion if available)
    if suggestions and suggestions[0][0]:
        default_slug = suggestions[0][0]

    # Create a table for style selection
    table = Table(title="🎨 Select DeepAI Image Generation Style", show_header=True)
    table.add_column("#", style="cyan", width=4)
    table.add_column("", width=2)  # Star column
    table.add_column("Style Name", style="green")
    table.add_column("Description", style="dim", max_width=50)

    # Find default index
    default_index = 0
    for idx, style in enumerate(styles, 1):
        if style.slug == default_slug:
            default_index = idx

        # Check if this is a suggested style
        star = ""
        name_prefix = ""
        name_suffix = ""
        if style.slug in suggestion_slugs:
            confidence, rank = suggestion_slugs[style.slug]
            star = "⭐" if rank == 1 else "✨"
            confidence_pct = int(confidence * 100)
            name_prefix = "[bold]"
            name_suffix = f"[/bold] [dim]({confidence_pct}%)[/dim]"

        # Apply bold for default
        if style.slug == default_slug and not name_prefix:
            name_prefix = "[bold]"
            name_suffix = "[/bold]"

        table.add_row(
            str(idx),
            star,
            f"{name_prefix}{style.name}{name_suffix}",
            (style.description[:47] + "..." if len(style.description) > 50 else style.description),
        )

    console.print(table)

    # Show default hint
    default_style_obj = styles[default_index - 1]
    if default_index > 0:
        console.print(
            f"\n[dim]Default: #{default_index} - {default_style_obj.name}"
            f"{' (Top recommendation)' if suggestions and suggestions[0][0] == default_style_obj.slug else ''}[/dim]"
        )

    # Get user selection
    while True:
        selection = console.input(
            "\n[bold cyan]Select style number (or press Enter for default):[/bold cyan] "
        ).strip()

        # Use default if empty
        if not selection:
            selected_style = styles[default_index - 1]
            break

        # Validate selection
        try:
            idx = int(selection)
            if 1 <= idx <= len(styles):
                selected_style = styles[idx - 1]
                break
            else:
                console.print(f"[red]Invalid selection. Please enter 1-{len(styles)}[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a number.[/red]")

    return selected_style.slug


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
                console.print(f"[red]Please enter a number between 1 and {len(files)}[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a number or 'q' to quit.[/red]")
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
    table = Table(title=f"💡 Generated {len(prompts)} Origami Prompts", show_header=True)
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
                console.print(f"[red]Please enter a number between 1 and {len(prompts)}[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a number or 'q' to quit.[/red]")
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
    table = Table(title=f"💡 Generated {len(prompts)} Origami Prompts", show_header=True)
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
def list_styles() -> None:
    """List all available DeepAI image generation styles"""
    loader = get_style_loader()
    styles = loader.list_styles()

    if not styles:
        console.print("[red]No styles found in configuration.[/red]")
        raise typer.Exit(1)

    # Create a detailed table
    table = Table(title="🎨 Available DeepAI Image Generation Styles", show_header=True)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Slug", style="yellow", width=30)
    table.add_column("Name", style="green", width=35)
    table.add_column("Description", style="dim")

    for idx, style in enumerate(styles, 1):
        table.add_row(
            str(idx),
            style.slug,
            style.name,
            style.description,
        )

    console.print(table)
    console.print(f"\n[bold]Total: {len(styles)} styles available[/bold]")
    console.print(
        "\n[dim]Use --deepai-style <slug> or interactive selection in generate command[/dim]"
    )


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
    deepai_style: str | None = typer.Option(
        None,
        "--deepai-style",
        "-ds",
        help="DeepAI style slug (skips interactive selection)",
    ),
    prompt_count: int = typer.Option(
        10,
        "--prompt-count",
        "-pc",
        min=1,
        max=20,
        help="Number of prompts to generate",
    ),
    width: int = typer.Option(
        1792,
        "--width",
        "-w",
        min=128,
        max=2048,
        help="Banner width (must be multiple of 32)",
    ),
    height: int = typer.Option(
        1024,
        "--height",
        "-h",
        min=128,
        max=2048,
        help="Banner height (must be multiple of 32)",
    ),
    version: Version = typer.Option(
        Version.genius,
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

    # Initialize clients early (GPT needed for style suggestions)
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

    # Get title for initial display
    title = front_matter.get("title", "Blog Post")
    tags = front_matter.get("tags", []) + front_matter.get("categories", [])

    # Show initial post info (without style yet)
    info_panel = Panel(
        f"[bold]Title:[/bold] {title}\n"
        f"[bold]Tags:[/bold] {', '.join(tags[:5]) if tags else 'None'}",
        title="📄 Post Info",
        border_style="blue",
    )
    console.print(info_panel)

    # Get style suggestions from GPT if style not provided via CLI
    style_suggestions: list[tuple[str, float, str]] | None = None
    if not deepai_style:
        # Get available styles for GPT to analyze
        style_loader = get_style_loader()
        all_styles = style_loader.list_styles()
        available_styles = [(s.slug, s.name, s.description) for s in all_styles]

        # Ask GPT to suggest styles based on content
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("🤖 Analyzing post and suggesting styles...", total=None)
            style_suggestions = gpt_client.suggest_styles(
                title=title,
                content=body,
                available_styles=available_styles,
                num_suggestions=5,
            )
            progress.update(task, completed=True)

    # Interactive style selection (with suggestions if available)
    if not deepai_style:
        console.print("\n")
        deepai_style = interactive_select_style(suggestions=style_suggestions)

    # Validate the selected style
    style_loader = get_style_loader()
    selected_style = style_loader.get_style(deepai_style)
    if not selected_style:
        console.print(f"[red]Invalid style: {deepai_style}[/red]")
        raise typer.Exit(1)

    console.print(f"\n✨ [green]Using style:[/green] {selected_style.name}")
    console.print(f"[dim]{selected_style.description}[/dim]\n")

    # Generate prompts using the new unified method
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"🤖 Asking ChatGPT to create {prompt_count} prompts for {selected_style.name}...",
            total=None,
        )
        prompts = gpt_client.generate_prompts(
            title=title,
            content=body,
            deepai_style_slug=deepai_style,
            num_prompts=prompt_count,
        )
        progress.update(task, completed=True)

    if not prompts:
        console.print("[red]❌ No prompts generated. Exiting.[/red]")
        raise typer.Exit(1)

    # Interactive prompt selection
    selected_indices = interactive_select_prompts(prompts)
    banner_prompts = [prompts[i] for i in selected_indices]

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
            console.print(f"\n🎨 [bold]Generating {len(banner_prompts)} banners...[/bold]")

        # Prepare batch data for async generation
        batch_data = [
            {
                "prompt": prompt,
                "output_path": output_path,
                "deepai_style": deepai_style,
                "width": width,
                "height": height,
                "version": version.value,
            }
            for prompt, output_path in zip(banner_prompts, output_paths, strict=False)
        ]

        # Generate all banners with async batch processing
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating banners...", total=len(banner_prompts))

            # Run async batch generation
            results = asyncio.run(deepai_client.generate_batch(batch_data))

            # Process results
            successful = 0
            failed = 0
            failed_prompts = []

            for success, output_path, prompt in zip(
                results, output_paths, banner_prompts, strict=False
            ):
                if success:
                    console.print(f"  ✓ [green]{output_path.name}[/green]")
                    successful += 1
                else:
                    console.print(f"  ✗ [red]{output_path.name}[/red]")
                    failed += 1
                    failed_prompts.append((output_path.name, prompt[:60]))

                progress.advance(task)

        # Enhanced summary
        if len(banner_prompts) == 1:
            if successful:
                console.print(
                    f"\n✨ [bold green]Done![/bold green] Banner saved to: [cyan]{output_paths[0]}[/cyan]"
                )
            else:
                console.print("\n[red]❌ Banner generation failed.[/red]")
                raise typer.Exit(1)
        else:
            total = successful + failed
            success_rate = (successful / total * 100) if total > 0 else 0

            console.print("\n✨ [bold green]Batch complete![/bold green]")
            console.print(f"  ✓ {successful} successful, ✗ {failed} failed")
            console.print(f"  Success rate: {success_rate:.1f}%")
            console.print(f"  [cyan]Output directory: {output_dir}[/cyan]")

            if failed_prompts:
                console.print("\n[yellow]Failed images:[/yellow]")
                for name, prompt_preview in failed_prompts:
                    console.print(f"  • {name}: {prompt_preview}...")


@app.command()
def direct(
    prompt: str = typer.Argument(..., help="Banner image prompt"),
    output: Path = typer.Option(
        Path("banner.png"),
        "--output",
        "-o",
        help="Output file path",
    ),
    deepai_style: str | None = typer.Option(
        None,
        "--deepai-style",
        "-ds",
        help="DeepAI style slug (skips interactive selection)",
    ),
    width: int = typer.Option(
        1792,
        "--width",
        "-w",
        min=128,
        max=2048,
        help="Banner width (must be multiple of 32)",
    ),
    height: int = typer.Option(
        1024,
        "--height",
        "-h",
        min=128,
        max=2048,
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

    # Interactive style selection if not provided
    if not deepai_style:
        console.print("\n")
        deepai_style = interactive_select_style()

    # Validate the selected style
    style_loader = get_style_loader()
    selected_style = style_loader.get_style(deepai_style)
    if not selected_style:
        console.print(f"[red]Invalid style: {deepai_style}[/red]")
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
            f"[bold]Style:[/bold] {selected_style.name}\n"
            f"[bold]Dimensions:[/bold] {width}x{height}\n"
            f"[bold]Version:[/bold] {version.value}\n"
            f"[bold]Output:[/bold] {output}",
            title="🎨 Generation Info",
            border_style="cyan",
        )
    )

    # Generate
    console.print("\n🎨 [bold]Generating banner...[/bold]")

    success = asyncio.run(
        deepai_client.generate_and_save(
            prompt=prompt,
            output_path=output,
            deepai_style=deepai_style,
            width=width,
            height=height,
            version=version.value,
        )
    )

    if success:
        console.print(f"\n✨ [bold green]Done![/bold green] Banner saved to: [cyan]{output}[/cyan]")
    else:
        console.print("\n[red]❌ Banner generation failed.[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
