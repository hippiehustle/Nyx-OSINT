"""Combined launcher for Nyx GUI and CLI."""

import sys
from typing import Optional


def is_cli_mode() -> bool:
    """Determine if we should run in CLI mode.
    
    Returns:
        True if CLI mode should be used, False for GUI mode
    """
    # Check if any arguments are provided (excluding script name)
    if len(sys.argv) > 1:
        # Check for CLI-specific flags
        cli_flags = ["--help", "-h", "--version", "-v", "search", "platforms", "stats", 
                     "categories", "help", "targets", "export", "config", "history", 
                     "update", "smart"]
        
        first_arg = sys.argv[1].lower()
        
        # If first argument is a CLI command, use CLI mode
        if first_arg in cli_flags or first_arg.startswith("-"):
            return True
        
        # If --cli flag is explicitly set
        if "--cli" in sys.argv or "-c" in sys.argv:
            return True
    
    # Default to GUI mode if no CLI indicators
    return False


def main():
    """Main launcher entry point."""
    if is_cli_mode():
        # Launch CLI
        from nyx.cli import main as cli_main
        cli_main()
    else:
        # Launch GUI
        from nyx.main import main as gui_main
        gui_main()


if __name__ == "__main__":
    main()

