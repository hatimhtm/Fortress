"""Command-line interface for Fortress password generator."""

import sys
from typing import Optional

try:
    import typer
    from typing_extensions import Annotated
    TYPER_AVAILABLE = True
except ImportError:
    TYPER_AVAILABLE = False

from fortress.core import (
    generate_password,
    generate_passphrase,
    PasswordConfig,
    calculate_entropy,
    get_strength_label,
    get_crack_time_estimate,
)
from fortress.utils.display import Display


def create_app() -> "typer.Typer":
    """Create the Typer CLI application."""
    if not TYPER_AVAILABLE:
        raise ImportError("typer is required for CLI. Install with: pip install typer")
    
    app = typer.Typer(
        name="fortress",
        help="🏰 Fortress - The Secure Password Generator",
        add_completion=False,
    )
    
    @app.command()
    def generate(
        length: Annotated[
            int, 
            typer.Option("--length", "-l", help="Password length")
        ] = 16,
        no_uppercase: Annotated[
            bool, 
            typer.Option("--no-uppercase", "-U", help="Exclude uppercase letters")
        ] = False,
        no_lowercase: Annotated[
            bool, 
            typer.Option("--no-lowercase", "-L", help="Exclude lowercase letters")
        ] = False,
        no_digits: Annotated[
            bool, 
            typer.Option("--no-digits", "-D", help="Exclude digits")
        ] = False,
        no_symbols: Annotated[
            bool, 
            typer.Option("--no-symbols", "-S", help="Exclude symbols")
        ] = False,
        exclude_ambiguous: Annotated[
            bool, 
            typer.Option("--exclude-ambiguous", "-x", help="Exclude ambiguous chars (0O1lI)")
        ] = False,
        count: Annotated[
            int, 
            typer.Option("--count", "-c", help="Number of passwords to generate")
        ] = 1,
        quiet: Annotated[
            bool, 
            typer.Option("--quiet", "-q", help="Output only the password(s)")
        ] = False,
    ) -> None:
        """Generate a secure password."""
        display = Display(use_rich=not quiet)
        
        if not quiet:
            display.print_header("🏰 Fortress Password Generator")
        
        try:
            config = PasswordConfig(
                length=length,
                use_uppercase=not no_uppercase,
                use_lowercase=not no_lowercase,
                use_digits=not no_digits,
                use_symbols=not no_symbols,
                exclude_ambiguous=exclude_ambiguous,
            )
        except ValueError as e:
            display.print_error(str(e))
            raise typer.Exit(code=1)
        
        for i in range(count):
            if not quiet and count == 1:
                display.show_generating()
            
            password = generate_password(config=config)
            
            if quiet:
                print(password)
            else:
                display.print_password(password)
                
                # Show strength info
                entropy = calculate_entropy(password)
                label, color = get_strength_label(entropy)
                crack_time = get_crack_time_estimate(entropy)
                display.print_strength(label, color, entropy, crack_time)
        
        if not quiet:
            display.print_info("\n💡 Tip: Use -q for quiet output (just the password)")
    
    @app.command()
    def passphrase(
        words: Annotated[
            int, 
            typer.Option("--words", "-w", help="Number of words")
        ] = 4,
        separator: Annotated[
            str, 
            typer.Option("--separator", "-s", help="Word separator")
        ] = "-",
        no_capitalize: Annotated[
            bool, 
            typer.Option("--no-capitalize", help="Don't capitalize words")
        ] = False,
        quiet: Annotated[
            bool, 
            typer.Option("--quiet", "-q", help="Output only the passphrase")
        ] = False,
    ) -> None:
        """Generate a memorable passphrase."""
        display = Display(use_rich=not quiet)
        
        if not quiet:
            display.print_header("🏰 Fortress Passphrase Generator")
            display.show_generating()
        
        phrase = generate_passphrase(
            word_count=words,
            separator=separator,
            capitalize=not no_capitalize,
        )
        
        if quiet:
            print(phrase)
        else:
            display.print_password(phrase)
            
            entropy = calculate_entropy(phrase)
            label, color = get_strength_label(entropy)
            crack_time = get_crack_time_estimate(entropy)
            display.print_strength(label, color, entropy, crack_time)
    
    @app.command()
    def check(
        password: Annotated[
            str, 
            typer.Argument(help="Password to analyze")
        ],
    ) -> None:
        """Check the strength of an existing password."""
        display = Display()
        
        display.print_header("🏰 Fortress Password Analyzer")
        
        entropy = calculate_entropy(password)
        label, color = get_strength_label(entropy)
        crack_time = get_crack_time_estimate(entropy)
        
        display.print_strength(label, color, entropy, crack_time)
    
    return app


def main() -> None:
    """Main entry point for the CLI."""
    if not TYPER_AVAILABLE:
        print("Error: typer is required. Install with: pip install 'fortress[cli]'")
        sys.exit(1)
    
    app = create_app()
    app()


if __name__ == "__main__":
    main()
