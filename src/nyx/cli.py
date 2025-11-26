"""CLI entry point for Nyx application."""

import asyncio
import sys
from typing import Optional

import click

from nyx import __version__
from nyx.config.base import load_config
from nyx.core.logger import setup_logging, get_logger
from nyx.osint.platforms import get_platform_database
from nyx.osint.search import SearchService
from nyx.intelligence.email import EmailIntelligence
from nyx.intelligence.phone import PhoneIntelligence

logger = get_logger(__name__)


@click.group()
@click.version_option(version=__version__, prog_name="nyx-cli")
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


@cli.command()
@click.argument("email")
@click.pass_context
def email(ctx, email):
    """Investigate email address."""

    async def async_email_check():
        email_intel = EmailIntelligence()
        result = await email_intel.investigate(email)

        click.echo(f"\nEmail Intelligence Report: {email}")
        click.echo("=" * 80)
        click.echo(f"Valid Format: {'✓' if result.valid else '✗'}")
        click.echo(f"Exists: {'✓' if result.exists else '✗'}")
        click.echo(f"Disposable: {'✓' if result.disposable else '✗'}")
        click.echo(f"Breached: {'✓' if result.breached else '✗'}")

        if result.breached:
            click.echo(f"Breach Count: {result.breach_count}")
            click.echo(f"Breaches: {', '.join(result.breaches)}")

        if result.providers:
            click.echo(f"Providers/Services: {', '.join(result.providers)}")

        click.echo(f"Reputation Score: {result.reputation_score:.1f}/100")
        click.echo(f"Checked At: {result.checked_at}")

    asyncio.run(async_email_check())


@cli.command()
@click.argument("phone")
@click.option("-r", "--region", help="Region code (e.g., US)", type=str)
@click.pass_context
def phone(ctx, phone, region):
    """Investigate phone number."""

    async def async_phone_check():
        phone_intel = PhoneIntelligence()
        result = await phone_intel.investigate(phone, region)

        click.echo(f"\nPhone Intelligence Report: {phone}")
        click.echo("=" * 80)
        click.echo(f"Valid: {'✓' if result.valid else '✗'}")

        if result.valid:
            click.echo(f"Country: {result.country_name} ({result.country_code})")
            click.echo(f"Location: {result.location or 'Unknown'}")
            click.echo(f"Carrier: {result.carrier or 'Unknown'}")
            click.echo(f"Line Type: {result.line_type}")
            click.echo(f"Timezones: {', '.join(result.timezones)}")
            click.echo(f"\nFormatted:")
            click.echo(f"  International: {result.formatted_international}")
            click.echo(f"  National: {result.formatted_national}")
            click.echo(f"  E164: {result.formatted_e164}")
            click.echo(f"Reputation Score: {result.reputation_score:.1f}/100")

            if result.metadata.get("social_platforms"):
                platforms = result.metadata["social_platforms"]
                click.echo(f"Social Platforms: {', '.join(platforms)}")

        click.echo(f"Checked At: {result.checked_at}")

    asyncio.run(async_phone_check())


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
