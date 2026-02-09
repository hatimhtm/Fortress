"""Terminal display utilities for Fortress CLI."""

import sys
import time
from typing import Optional

# Try to import rich for enhanced terminal output
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.panel import Panel
    from rich.text import Text
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class Display:
    """Terminal display handler with fallback for basic terminals."""
    
    def __init__(self, use_rich: bool = True):
        """Initialize display.
        
        Args:
            use_rich: Whether to use rich library for enhanced output.
        """
        self.use_rich = use_rich and RICH_AVAILABLE
        if self.use_rich:
            self.console = Console()
    
    def print_header(self, text: str) -> None:
        """Print a styled header."""
        if self.use_rich:
            self.console.print(Panel(text, style="bold green"))
        else:
            print(f"\n{'='*50}")
            print(f"  {text}")
            print(f"{'='*50}\n")
    
    def print_password(self, password: str) -> None:
        """Print the generated password with styling."""
        if self.use_rich:
            self.console.print("\n[bold white]Your Password:[/bold white]")
            self.console.print(Panel(password, style="bold cyan", expand=False))
        else:
            print(f"\nYour Password:\n{password}\n")
    
    def print_strength(
        self, 
        label: str, 
        color: str, 
        entropy: float,
        crack_time: str,
    ) -> None:
        """Print password strength indicator."""
        if self.use_rich:
            # Create a visual strength bar
            if color == "red":
                bar_filled = 2
            elif color == "bright_red":
                bar_filled = 4
            elif color == "yellow":
                bar_filled = 6
            elif color == "green":
                bar_filled = 8
            else:
                bar_filled = 10
                
            bar = f"[{color}]{'█' * bar_filled}[/{color}]{'░' * (10 - bar_filled)}"
            
            self.console.print(f"\n[bold]Strength:[/bold] {bar} [{color}]{label}[/{color}]")
            self.console.print(f"[dim]Entropy: {entropy:.1f} bits[/dim]")
            self.console.print(f"[dim]Crack time: {crack_time}[/dim]")
        else:
            bar = "#" * (int(entropy / 12)) + "-" * (10 - int(entropy / 12))
            print(f"\nStrength: [{bar}] {label}")
            print(f"Entropy: {entropy:.1f} bits")
            print(f"Crack time: {crack_time}")
    
    def print_error(self, message: str) -> None:
        """Print an error message."""
        if self.use_rich:
            self.console.print(f"[bold red]Error:[/bold red] {message}")
        else:
            print(f"Error: {message}", file=sys.stderr)
    
    def print_success(self, message: str) -> None:
        """Print a success message."""
        if self.use_rich:
            self.console.print(f"[bold green]✓[/bold green] {message}")
        else:
            print(f"✓ {message}")
    
    def print_info(self, message: str) -> None:
        """Print an info message."""
        if self.use_rich:
            self.console.print(f"[dim]{message}[/dim]")
        else:
            print(message)
    
    def show_generating(self) -> None:
        """Show a generating animation."""
        if self.use_rich:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description="Generating secure password...", total=None)
                time.sleep(0.5)
        else:
            print("Generating password...", end="", flush=True)
            time.sleep(0.3)
            print(" done!")
