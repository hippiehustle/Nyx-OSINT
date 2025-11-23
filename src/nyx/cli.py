"""CLI entry point for Nyx application."""

import asyncio
import sys
from typing import Optional

import click

from nyx.config.base import load_config
from nyx.core.logger import setup_logging, get_logger
from nyx.osint.platforms import get_platform_database
from nyx.osint.search import SearchService

logger = get_logger(__name__)


@click.group()
@click.option("-c", "--config", help="Configuration file path", type=str)
@click.option("-d", "--debug", help="Enable debug mode", is_flag=True)
@click.pass_context
def cli(ctx, config, debug):
    """Nyx CLI - OSINT Investigation Platform."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["debug"] = debug

    # Load configuration and setup logging
    cfg = load_config(config)
    setup_logging(
        level="DEBUG" if debug else cfg.logging.level,
        log_file=cfg.logging.file_path,
    )
    ctx.obj["config"] = cfg


@cli.command()
@click.argument("username")
@click.option(
    "-e",
    "--exclude-nsfw",
    help="Exclude NSFW platforms",
    is_flag=True,
)
@click.option(
    "-t",
    "--timeout",
    help="Search timeout in seconds",
    type=int,
)
@click.pass_context
def search(ctx, username, exclude_nsfw, timeout):
    """Search for username across platforms."""
    config = ctx.obj["config"]

    async def async_search():
        search_service = SearchService()
        results = await search_service.search_username(
            username,
            exclude_nsfw=exclude_nsfw,
            timeout=timeout,
        )

        if not results:
            click.echo(f"No profiles found for username: {username}")
            return

        click.echo(f"\nFound {len(results)} profiles:")
        click.echo("-" * 80)

        for platform, result in sorted(results.items()):
            click.echo(f"\n{platform}:")
            click.echo(f"  URL: {result.get('url')}")
            if result.get("response_time"):
                click.echo(f"  Response Time: {result['response_time']:.2f}s")

    asyncio.run(async_search())


@cli.command()
@click.option(
    "-c",
    "--category",
    help="Filter by category",
    multiple=True,
)
@click.pass_context
def platforms(ctx, category):
    """List configured platforms."""
    db = get_platform_database()

    if category:
        platforms_list = []
        for cat in category:
            from nyx.models.platform import PlatformCategory

            try:
                cat_enum = PlatformCategory[cat.upper()]
                platforms_list.extend(db.get_by_category(cat_enum))
            except KeyError:
                click.echo(f"Unknown category: {cat}")
    else:
        platforms_list = list(db.platforms.values())

    if not platforms_list:
        click.echo("No platforms found")
        return

    click.echo(f"\nConfigured Platforms ({len(platforms_list)}):")
    click.echo("-" * 80)

    for platform in sorted(platforms_list, key=lambda p: p.name):
        status = "✓" if platform.is_active else "✗"
        nsfw_marker = " [NSFW]" if platform.is_nsfw else ""
        click.echo(f"{status} {platform.name}{nsfw_marker}")
        click.echo(f"  Category: {platform.category.value}")
        click.echo(f"  URL: {platform.url}")


@cli.command()
@click.pass_context
def stats(ctx):
    """Show platform statistics."""
    service = SearchService()
    stats = service.get_platform_stats()

    click.echo("\nPlatform Statistics:")
    click.echo("-" * 40)
    click.echo(f"Total Platforms: {stats['total_platforms']}")
    click.echo(f"Active Platforms: {stats['active_platforms']}")
    click.echo(f"NSFW Platforms: {stats['nsfw_platforms']}")
    click.echo(f"SFW Platforms: {stats['sfw_platforms']}")


def main():
    """Main CLI entry point."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        click.echo("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
