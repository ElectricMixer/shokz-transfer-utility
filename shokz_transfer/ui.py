"""Terminal UI helpers for tables, selection, and progress display."""

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from .indexer import Track

# Shared console instance
console = Console()


def display_tracks(tracks: list[Track], title: str = "Results") -> None:
    """Display tracks as a numbered table.

    Args:
        tracks: List of tracks to display.
        title: Table title.
    """
    if not tracks:
        console.print("[yellow]No tracks found.[/yellow]")
        return

    table = Table(title=title)
    table.add_column("#", justify="right", style="cyan", width=4)
    table.add_column("Title", style="white", max_width=35, overflow="ellipsis")
    table.add_column("Artist", style="green", max_width=25, overflow="ellipsis")
    table.add_column("Album", style="blue", max_width=25, overflow="ellipsis")
    table.add_column("Size", justify="right", style="magenta", width=8)

    for i, track in enumerate(tracks, start=1):
        table.add_row(
            str(i),
            track.title,
            track.artist,
            track.album,
            f"{track.size_mb:.1f} MB",
        )

    console.print(table)
    console.print(f"[dim]{len(tracks)} tracks[/dim]")


def display_playlist(tracks: list[Track], capacity_mb: int) -> None:
    """Display the current playlist with size totals.

    Args:
        tracks: List of tracks in playlist.
        capacity_mb: Maximum capacity in MB.
    """
    if not tracks:
        console.print("[yellow]Playlist is empty.[/yellow]")
        return

    total_mb = sum(t.size_mb for t in tracks)
    percent = (total_mb / capacity_mb) * 100

    # Color based on capacity usage
    if percent > 100:
        color = "red"
    elif percent > 90:
        color = "yellow"
    else:
        color = "green"

    table = Table(title="Current Playlist")
    table.add_column("#", justify="right", style="cyan", width=4)
    table.add_column("Title", style="white", max_width=35, overflow="ellipsis")
    table.add_column("Artist", style="green", max_width=25, overflow="ellipsis")
    table.add_column("Size", justify="right", style="magenta", width=8)

    for i, track in enumerate(tracks, start=1):
        table.add_row(
            str(i),
            track.title,
            track.artist,
            f"{track.size_mb:.1f} MB",
        )

    console.print(table)
    console.print(
        f"[{color}]{len(tracks)} tracks, {total_mb:.1f} MB / {capacity_mb} MB ({percent:.0f}%)[/{color}]"
    )

    if percent > 100:
        console.print("[red bold]Warning: Playlist exceeds Shokz capacity![/red bold]")


def parse_selection(input_str: str, max_value: int) -> list[int]:
    """Parse selection input like '1, 3, 5-7' into a list of indices.

    Args:
        input_str: User input string (e.g., "1, 3, 5-7" or "all").
        max_value: Maximum valid value (number of items in list).

    Returns:
        List of 0-based indices (sorted, deduplicated).
        Returns empty list on invalid input.
    """
    input_str = input_str.strip().lower()

    # Handle special cases
    if input_str in ("all", "*"):
        return list(range(max_value))

    if input_str in ("none", ""):
        return []

    indices = set()

    # Split by comma and process each part
    parts = input_str.replace(" ", "").split(",")

    for part in parts:
        if not part:
            continue

        if "-" in part:
            # Range like "5-7"
            try:
                start, end = part.split("-", 1)
                start_num = int(start)
                end_num = int(end)

                # Validate range
                if start_num < 1 or end_num > max_value or start_num > end_num:
                    continue

                for i in range(start_num, end_num + 1):
                    indices.add(i - 1)  # Convert to 0-based
            except ValueError:
                continue
        else:
            # Single number like "3"
            try:
                num = int(part)
                if 1 <= num <= max_value:
                    indices.add(num - 1)  # Convert to 0-based
            except ValueError:
                continue

    return sorted(indices)


def prompt_selection(tracks: list[Track]) -> list[Track]:
    """Display tracks and prompt user for selection.

    Args:
        tracks: List of tracks to choose from.

    Returns:
        List of selected tracks.
    """
    if not tracks:
        return []

    display_tracks(tracks)
    console.print()
    console.print("[dim]Select tracks (e.g., 1,3,5-7) or 'all' or 'none':[/dim]")

    user_input = console.input("[cyan]> [/cyan]")
    indices = parse_selection(user_input, len(tracks))

    return [tracks[i] for i in indices]


def prompt_menu(title: str, options: list[str]) -> int:
    """Display a numbered menu and get user choice.

    Args:
        title: Menu title.
        options: List of menu options.

    Returns:
        0-based index of selected option, or -1 if invalid.
    """
    console.print(f"\n[bold]{title}[/bold]")
    for i, option in enumerate(options, start=1):
        console.print(f"  {i}. {option}")

    console.print()
    user_input = console.input("[cyan]> [/cyan]").strip()

    try:
        choice = int(user_input)
        if 1 <= choice <= len(options):
            return choice - 1
    except ValueError:
        pass

    return -1


def prompt_input(prompt: str) -> str:
    """Prompt user for text input.

    Args:
        prompt: Prompt message.

    Returns:
        User input string.
    """
    console.print(f"[dim]{prompt}[/dim]")
    return console.input("[cyan]> [/cyan]").strip()


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]{message}[/green]")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]{message}[/red]")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]{message}[/yellow]")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[blue]{message}[/blue]")


def create_progress() -> Progress:
    """Create a progress bar for long operations."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    )
