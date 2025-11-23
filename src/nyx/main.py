"""Main entry point for Nyx application."""

import asyncio
import sys
from typing import Optional

from nyx.config.base import load_config
from nyx.core.logger import setup_logging, get_logger
from nyx.gui.main_window import create_app

logger = get_logger(__name__)


async def async_main(config_path: Optional[str] = None) -> None:
    """Async main function.

    Args:
        config_path: Path to configuration file
    """
    # Load configuration
    config = load_config(config_path)

    # Setup logging
    setup_logging(
        level=config.logging.level,
        log_file=config.logging.file_path,
        max_file_size=config.logging.max_file_size,
        backup_count=config.logging.backup_count,
    )

    logger.info(f"Nyx v0.1.0 started")
    logger.info(f"Configuration loaded: {config_path or 'default'}")
    logger.debug(f"Debug mode: {config.debug}")


def main(config_path: Optional[str] = None) -> None:
    """Main entry point for Nyx application.

    Args:
        config_path: Optional path to configuration file
    """
    # Run async initialization
    asyncio.run(async_main(config_path))

    # Create and run GUI application
    app = create_app()
    logger.info("GUI application started")

    try:
        app.mainloop()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Nyx - OSINT Investigation Platform",
        prog="nyx",
    )
    parser.add_argument(
        "-c",
        "--config",
        help="Path to configuration file",
        type=str,
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="Enable debug mode",
        action="store_true",
    )

    args = parser.parse_args()

    main(config_path=args.config)
