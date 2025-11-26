"""CLI entry point for Nyx OSINT application.

This module provides a comprehensive command-line interface for OSINT investigations,
including username searches across 200+ platforms, email intelligence gathering,
phone number lookups, and platform management.
"""

import asyncio
import logging
import sys
from typing import Optional, List

import click

from nyx import __version__
from nyx.config.base import load_config
from nyx.core.logger import setup_logging, get_logger
from nyx.osint.platforms import get_platform_database
from nyx.osint.search import SearchService
from nyx.intelligence.email import EmailIntelligence
from nyx.intelligence.phone import PhoneIntelligence
from nyx.models.platform import PlatformCategory

logger = get_logger(__name__)

# Configure logging for cleaner CLI output
logging.getLogger("nyx.osint.search").setLevel(logging.WARNING)


# ============================================================================
# Main CLI Group
# ============================================================================

@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="nyx-cli")
@click.option("-c", "--config", help="Path to configuration file", type=str, metavar="FILE")
@click.option("-d", "--debug", help="Enable debug logging", is_flag=True)
@click.pass_context
def cli(ctx, config, debug):
    """🔍 Nyx OSINT - Professional Intelligence Gathering Platform

    \b
    Nyx is a comprehensive OSINT tool for investigating usernames, emails,
    and phone numbers across 200+ platforms including social media, dating
    sites, forums, gaming networks, and adult platforms.

    \b
    🌟 KEY FEATURES:
    • Search 200+ platforms simultaneously
    • Email intelligence & breach detection
    • Phone number investigation
    • Advanced filtering & categorization
    • NSFW platform support
    • Export results in multiple formats

    \b
    📚 QUICK START:

      # Search for a username across all platforms
      nyx-cli search -u johndoe

      # Search username excluding NSFW platforms
      nyx-cli search -u johndoe --no-nsfw

      # Investigate an email address
      nyx-cli search -e john@example.com

      # Search a phone number
      nyx-cli search -p +15551234567

      # List all available platforms
      nyx-cli platforms

      # Show platform statistics
      nyx-cli stats

    \b
    📖 For detailed help on any command, use:
      nyx-cli COMMAND --help

    \b
    🔗 Documentation: docs/USER_MANUAL.md
    🐛 Issues: https://github.com/your-org/nyx-osint/issues
    """
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["debug"] = debug

    # Only load config if a subcommand will be invoked
    # This allows --version and --help to work without config files
    if ctx.invoked_subcommand is not None:
        try:
            cfg = load_config(config)
            setup_logging(
                level="DEBUG" if debug else cfg.logging.level,
                log_file=cfg.logging.file_path,
            )
            ctx.obj["config"] = cfg
        except Exception as e:
            click.echo(f"❌ Error loading configuration: {e}", err=True)
            click.echo("💡 Run with a valid configuration or create default config files.", err=True)
            sys.exit(1)
    elif ctx.invoked_subcommand is None and not ctx.resilient_parsing:
        # No subcommand provided, show help
        click.echo(ctx.get_help())


# ============================================================================
# Unified Search Command
# ============================================================================

@cli.command()
@click.option(
    "-u", "--username",
    help="Search for a username across platforms",
    metavar="USERNAME",
)
@click.option(
    "-e", "--email",
    help="Investigate an email address",
    metavar="EMAIL",
)
@click.option(
    "-p", "--phone",
    help="Investigate a phone number",
    metavar="PHONE",
)
@click.option(
    "--platforms",
    "-P",
    help="Specific platforms to search (comma-separated)",
    metavar="PLATFORMS",
)
@click.option(
    "--category",
    "-C",
    multiple=True,
    help="Filter by category (can be used multiple times)",
    type=click.Choice([
        "social_media", "professional", "dating", "gaming",
        "forums", "adult", "blogging", "photography",
        "messaging", "streaming", "crypto", "shopping", "other"
    ], case_sensitive=False),
)
@click.option(
    "--no-nsfw",
    is_flag=True,
    help="Exclude NSFW/adult platforms from search",
)
@click.option(
    "--only-nsfw",
    is_flag=True,
    help="Search ONLY NSFW/adult platforms",
)
@click.option(
    "-t", "--timeout",
    type=int,
    default=120,
    help="Search timeout in seconds (default: 120)",
    metavar="SECONDS",
    show_default=True,
)
@click.option(
    "-o", "--output",
    type=click.Choice(["compact", "detailed", "json"], case_sensitive=False),
    default="detailed",
    help="Output format (default: detailed)",
    show_default=True,
)
@click.option(
    "--save",
    type=click.Path(),
    help="Save results to file (auto-detects format from extension)",
    metavar="FILE",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Show verbose output including failed searches",
)
@click.option(
    "--region",
    help="Region code for phone number (e.g., US, GB)",
    metavar="CODE",
)
@click.pass_context
def search(
    ctx,
    username,
    email,
    phone,
    platforms,
    category,
    no_nsfw,
    only_nsfw,
    timeout,
    output,
    save,
    verbose,
    region,
):
    """🔎 Unified search command for all OSINT investigations

    \b
    This command provides a unified interface for searching usernames, emails,
    and phone numbers. Specify the type of search using the appropriate flag.

    \b
    📋 SEARCH TYPES:

      Username Search:
        Search for a username across all configured platforms
        Example: nyx-cli search -u johndoe

      Email Intelligence:
        Investigate email addresses, check breaches, validate
        Example: nyx-cli search -e john@example.com

      Phone Investigation:
        Lookup phone numbers, carrier info, location
        Example: nyx-cli search -p +15551234567 --region US

    \b
    🎯 ADVANCED FILTERING:

      # Search specific platforms only
      nyx-cli search -u johndoe --platforms "Twitter,Instagram,GitHub"

      # Search only social media platforms
      nyx-cli search -u johndoe --category social_media

      # Search multiple categories
      nyx-cli search -u johndoe -C social_media -C professional

      # Exclude NSFW platforms
      nyx-cli search -u johndoe --no-nsfw

      # Search ONLY adult platforms
      nyx-cli search -u johndoe --only-nsfw

    \b
    💾 OUTPUT OPTIONS:

      # Compact output (URLs only)
      nyx-cli search -u johndoe -o compact

      # JSON output for parsing
      nyx-cli search -u johndoe -o json

      # Save results to file
      nyx-cli search -u johndoe --save results.json

      # Verbose mode (show failed searches)
      nyx-cli search -u johndoe -v

    \b
    ⏱️ PERFORMANCE:

      # Adjust timeout for slow connections
      nyx-cli search -u johndoe --timeout 60

      # Quick search with short timeout
      nyx-cli search -u johndoe -t 10

    \b
    📌 NOTES:
    • You must specify at least one of: -u, -e, or -p
    • --no-nsfw and --only-nsfw are mutually exclusive
    • Platform names are case-insensitive
    • Results are sorted by platform name
    """
    # Validation
    if not (username or email or phone):
        click.echo("❌ Error: You must specify at least one search type:", err=True)
        click.echo("  -u/--username    Search for username", err=True)
        click.echo("  -e/--email       Investigate email", err=True)
        click.echo("  -p/--phone       Investigate phone", err=True)
        click.echo("\n💡 Use 'nyx-cli search --help' for more information", err=True)
        sys.exit(1)

    if no_nsfw and only_nsfw:
        click.echo("❌ Error: --no-nsfw and --only-nsfw are mutually exclusive", err=True)
        sys.exit(1)

    if len([x for x in [username, email, phone] if x]) > 1:
        click.echo("❌ Error: Specify only ONE search type at a time", err=True)
        sys.exit(1)

    # Execute appropriate search
    if username:
        _search_username(
            username=username,
            platforms_str=platforms,
            categories=category,
            exclude_nsfw=no_nsfw,
            only_nsfw=only_nsfw,
            timeout=timeout,
            output_format=output,
            save_file=save,
            verbose=verbose,
        )
    elif email:
        _search_email(
            email=email,
            timeout=timeout,
            output_format=output,
            save_file=save,
            verbose=verbose,
        )
    elif phone:
        _search_phone(
            phone=phone,
            region=region,
            timeout=timeout,
            output_format=output,
            save_file=save,
            verbose=verbose,
        )


def _search_username(
    username: str,
    platforms_str: Optional[str],
    categories: tuple,
    exclude_nsfw: bool,
    only_nsfw: bool,
    timeout: int,
    output_format: str,
    save_file: Optional[str],
    verbose: bool,
):
    """Execute username search."""
    async def async_search():
        import sys

        search_service = SearchService()

        # Parse platforms if provided
        platform_list = None
        if platforms_str:
            platform_list = [p.strip() for p in platforms_str.split(",")]

        # Convert categories to list
        category_list = list(categories) if categories else None

        # Handle NSFW filtering
        nsfw_filter = exclude_nsfw
        if only_nsfw:
            category_list = ["adult"]
            nsfw_filter = False

        click.echo(f"🔍 Searching for username: {username}")
        if platform_list:
            click.echo(f"📌 Platforms: {', '.join(platform_list)}")
        if category_list:
            click.echo(f"📂 Categories: {', '.join(category_list)}")
        if nsfw_filter:
            click.echo("🚫 Excluding NSFW platforms")
        if only_nsfw:
            click.echo("🔞 Searching ONLY NSFW platforms")
        click.echo(f"⏱️  Timeout: {timeout}s")
        click.echo("")

        # Progress tracking
        checked_count = [0]
        found_count = [0]
        total_platforms = [0]

        def show_progress(platform_name: str, status: str):
            """Show search progress in a user-friendly way."""
            if status == "checking":
                checked_count[0] += 1
                # Show a simple progress indicator
                if checked_count[0] == 1 or checked_count[0] % 10 == 0 or status == "found":
                    click.echo(f"⏳ Checking {checked_count[0]}/{total_platforms[0]} platforms...", nl=False)
                    click.echo("\r", nl=False)
                    sys.stdout.flush()
            elif status == "found":
                found_count[0] += 1
                click.echo(f"✓ Found on {platform_name}" + " " * 30)

        # Count total platforms that will be searched
        from nyx.osint.platforms import get_platform_database
        db = get_platform_database()
        platforms_dict = {}
        for name, platform in db.platforms.items():
            if not platform.is_active:
                continue
            if nsfw_filter and platform.is_nsfw:
                continue
            if platform_list and platform.name.lower() not in [p.lower() for p in platform_list]:
                continue
            if category_list and platform.category.value not in [c.lower() for c in category_list]:
                continue
            platforms_dict[name] = platform

        total_platforms[0] = len(platforms_dict)
        click.echo(f"🔎 Searching {total_platforms[0]} platforms...\n")

        results = await search_service.search_username(
            username=username,
            platforms=platform_list,
            categories=category_list,
            exclude_nsfw=nsfw_filter,
            timeout=timeout,
        )

        # Clear progress line
        click.echo("\r" + " " * 80 + "\r", nl=False)

        if not results:
            click.echo("❌ No profiles found")
            return

        # Display results based on format
        if output_format == "compact":
            click.echo(f"\n✅ Found {len(results)} profiles:\n")
            for platform, result in sorted(results.items()):
                click.echo(f"  {result.get('url')}")

        elif output_format == "json":
            import json
            click.echo(json.dumps(results, indent=2))

        else:  # detailed
            click.echo(f"\n✅ Found {len(results)} profiles:")
            click.echo("=" * 80)

            for platform, result in sorted(results.items()):
                click.echo(f"\n🌐 {platform}:")
                click.echo(f"   URL: {result.get('url')}")
                if result.get("response_time"):
                    click.echo(f"   Response Time: {result['response_time']:.2f}s")
                if result.get("http_status"):
                    click.echo(f"   HTTP Status: {result['http_status']}")

        # Save if requested
        if save_file:
            import json
            with open(save_file, 'w') as f:
                json.dump(results, f, indent=2)
            click.echo(f"\n💾 Results saved to: {save_file}")

    asyncio.run(async_search())


def _search_email(
    email: str,
    timeout: int,
    output_format: str,
    save_file: Optional[str],
    verbose: bool,
):
    """Execute email search."""
    async def async_email_check():
        click.echo(f"📧 Investigating email: {email}\n")

        email_intel = EmailIntelligence()
        result = await email_intel.investigate(email)

        if output_format == "json":
            import json
            click.echo(json.dumps(result.__dict__, indent=2, default=str))
        else:
            click.echo("=" * 80)
            click.echo(f"📊 Email Intelligence Report")
            click.echo("=" * 80)
            click.echo(f"\n📬 Address: {email}")
            click.echo(f"✅ Valid Format: {'Yes' if result.valid else 'No'}")
            click.echo(f"📮 Exists: {'Yes' if result.exists else 'Unknown'}")
            click.echo(f"🗑️  Disposable: {'Yes' if result.disposable else 'No'}")
            click.echo(f"🚨 Breached: {'Yes' if result.breached else 'No'}")

            if result.breached:
                click.echo(f"\n⚠️  BREACH INFORMATION:")
                click.echo(f"   Count: {result.breach_count}")
                if result.breaches:
                    click.echo(f"   Breaches: {', '.join(result.breaches)}")

            if result.providers:
                click.echo(f"\n🏢 Associated Providers:")
                for provider in result.providers:
                    click.echo(f"   • {provider}")

            click.echo(f"\n⭐ Reputation Score: {result.reputation_score:.1f}/100")
            click.echo(f"🕐 Checked: {result.checked_at}")

        if save_file:
            import json
            with open(save_file, 'w') as f:
                json.dump(result.__dict__, f, indent=2, default=str)
            click.echo(f"\n💾 Results saved to: {save_file}")

    asyncio.run(async_email_check())


def _search_phone(
    phone: str,
    region: Optional[str],
    timeout: int,
    output_format: str,
    save_file: Optional[str],
    verbose: bool,
):
    """Execute phone search."""
    async def async_phone_check():
        click.echo(f"📱 Investigating phone: {phone}")
        if region:
            click.echo(f"🌍 Region: {region}")
        click.echo("")

        phone_intel = PhoneIntelligence()
        result = await phone_intel.investigate(phone, region)

        if output_format == "json":
            import json
            click.echo(json.dumps(result.__dict__, indent=2, default=str))
        else:
            click.echo("=" * 80)
            click.echo(f"📊 Phone Intelligence Report")
            click.echo("=" * 80)
            click.echo(f"\n📞 Number: {phone}")
            click.echo(f"✅ Valid: {'Yes' if result.valid else 'No'}")

            if result.valid:
                click.echo(f"\n🌍 LOCATION:")
                click.echo(f"   Country: {result.country_name} ({result.country_code})")
                click.echo(f"   Location: {result.location or 'Unknown'}")
                click.echo(f"   Timezones: {', '.join(result.timezones)}")

                click.echo(f"\n📡 CARRIER:")
                click.echo(f"   Carrier: {result.carrier or 'Unknown'}")
                click.echo(f"   Line Type: {result.line_type}")

                click.echo(f"\n🔢 FORMATS:")
                click.echo(f"   International: {result.formatted_international}")
                click.echo(f"   National: {result.formatted_national}")
                click.echo(f"   E164: {result.formatted_e164}")

                click.echo(f"\n⭐ Reputation Score: {result.reputation_score:.1f}/100")

                if result.metadata.get("social_platforms"):
                    platforms = result.metadata["social_platforms"]
                    click.echo(f"\n🌐 Social Platforms:")
                    for platform in platforms:
                        click.echo(f"   • {platform}")

            click.echo(f"\n🕐 Checked: {result.checked_at}")

        if save_file:
            import json
            with open(save_file, 'w') as f:
                json.dump(result.__dict__, f, indent=2, default=str)
            click.echo(f"\n💾 Results saved to: {save_file}")

    asyncio.run(async_phone_check())


# ============================================================================
# Platform Management Commands
# ============================================================================

@cli.command()
@click.option(
    "-c", "--category",
    multiple=True,
    help="Filter by category (can be used multiple times)",
    type=click.Choice([
        "social_media", "professional", "dating", "gaming",
        "forums", "adult", "blogging", "photography",
        "messaging", "streaming", "crypto", "shopping", "other"
    ], case_sensitive=False),
)
@click.option(
    "--nsfw",
    is_flag=True,
    help="Show only NSFW platforms",
)
@click.option(
    "--active-only",
    is_flag=True,
    help="Show only active platforms",
)
@click.option(
    "--count",
    is_flag=True,
    help="Show count only, not full list",
)
@click.pass_context
def platforms(ctx, category, nsfw, active_only, count):
    """📋 List and manage configured platforms

    \b
    Display all available platforms with detailed information including
    categories, URLs, and NSFW status. Supports filtering by category
    and NSFW content.

    \b
    EXAMPLES:

      # List all platforms
      nyx-cli platforms

      # List only social media platforms
      nyx-cli platforms --category social_media

      # List dating and adult platforms
      nyx-cli platforms -c dating -c adult

      # List only NSFW platforms
      nyx-cli platforms --nsfw

      # Show count of platforms by category
      nyx-cli platforms --category gaming --count

      # List only active platforms
      nyx-cli platforms --active-only

    \b
    CATEGORIES:
      social_media  - Facebook, Twitter, Instagram, etc.
      professional  - LinkedIn, GitHub, Stack Overflow, etc.
      dating        - Tinder, Bumble, OkCupid, etc.
      gaming        - Steam, Xbox, PlayStation, etc.
      forums        - Reddit, 4chan, Hacker News, etc.
      adult         - OnlyFans, Pornhub, Chaturbate, etc.
      blogging      - Medium, WordPress, Substack, etc.
      photography   - Flickr, 500px, Unsplash, etc.
      messaging     - Discord, Telegram, WhatsApp, etc.
      streaming     - Twitch, YouTube, Kick, etc.
      crypto        - Coinbase, OpenSea, Rarible, etc.
      shopping      - eBay, Etsy, Amazon, etc.
      other         - Music, funding, and misc platforms
    """
    db = get_platform_database()

    # Filter platforms
    if category:
        platforms_list = []
        for cat in category:
            try:
                cat_enum = PlatformCategory[cat.upper()]
                platforms_list.extend(db.get_by_category(cat_enum))
            except KeyError:
                click.echo(f"❌ Unknown category: {cat}")
                return
    else:
        platforms_list = list(db.platforms.values())

    # Apply NSFW filter
    if nsfw:
        platforms_list = [p for p in platforms_list if p.is_nsfw]

    # Apply active filter
    if active_only:
        platforms_list = [p for p in platforms_list if p.is_active]

    if not platforms_list:
        click.echo("❌ No platforms found matching criteria")
        return

    # Show count only if requested
    if count:
        click.echo(f"📊 Platform Count: {len(platforms_list)}")
        return

    # Group by category for better display
    from collections import defaultdict
    by_category = defaultdict(list)
    for platform in platforms_list:
        by_category[platform.category.value].append(platform)

    click.echo(f"\n📋 Configured Platforms ({len(platforms_list)} total)")
    click.echo("=" * 80)

    for cat, plats in sorted(by_category.items()):
        click.echo(f"\n🏷️  {cat.upper().replace('_', ' ')} ({len(plats)})")
        click.echo("-" * 80)

        for platform in sorted(plats, key=lambda p: p.name):
            status = "✓" if platform.is_active else "✗"
            nsfw_marker = " 🔞" if platform.is_nsfw else ""
            click.echo(f"  {status} {platform.name}{nsfw_marker}")
            click.echo(f"     {platform.url}")


@cli.command()
@click.option(
    "--by-category",
    is_flag=True,
    help="Show breakdown by category",
)
@click.pass_context
def stats(ctx, by_category):
    """📊 Display platform statistics and analytics

    \b
    Shows comprehensive statistics about configured platforms including
    total counts, category breakdowns, NSFW counts, and active platforms.

    \b
    EXAMPLES:

      # Show overall statistics
      nyx-cli stats

      # Show detailed breakdown by category
      nyx-cli stats --by-category
    """
    service = SearchService()
    stats_data = service.get_platform_stats()
    db = get_platform_database()

    click.echo("\n📊 Platform Statistics")
    click.echo("=" * 80)
    click.echo(f"\n📈 OVERVIEW:")
    click.echo(f"   Total Platforms: {stats_data['total_platforms']}")
    click.echo(f"   Active Platforms: {stats_data['active_platforms']}")
    click.echo(f"   Inactive Platforms: {stats_data['total_platforms'] - stats_data['active_platforms']}")
    click.echo(f"\n🔞 CONTENT RATING:")
    click.echo(f"   NSFW Platforms: {stats_data['nsfw_platforms']}")
    click.echo(f"   SFW Platforms: {stats_data['sfw_platforms']}")

    if by_category:
        from collections import Counter
        categories = Counter(p.category.value for p in db.platforms.values())

        click.echo(f"\n📂 BY CATEGORY:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            click.echo(f"   {cat.replace('_', ' ').title():<20} {count:>3}")


# ============================================================================
# Utility Commands
# ============================================================================

@cli.command()
@click.pass_context
def categories(ctx):
    """📂 List all available platform categories

    \b
    Displays all platform categories with descriptions and example platforms.
    Useful for understanding what platforms fall under each category.
    """
    categories_info = {
        "social_media": ("Social Media", "Facebook, Twitter, Instagram, TikTok, Snapchat"),
        "professional": ("Professional Networks", "LinkedIn, GitHub, Stack Overflow, AngelList"),
        "dating": ("Dating Platforms", "Tinder, Bumble, OkCupid, Match, Hinge"),
        "gaming": ("Gaming Platforms", "Steam, Xbox Live, PlayStation, Roblox, Minecraft"),
        "forums": ("Forums & Communities", "Reddit, 4chan, Quora, Hacker News"),
        "adult": ("Adult/NSFW Platforms", "OnlyFans, Pornhub, Chaturbate, FetLife"),
        "blogging": ("Blogging Platforms", "Medium, WordPress, Substack, Tumblr"),
        "photography": ("Photography & Art", "Flickr, 500px, DeviantArt, Unsplash"),
        "messaging": ("Messaging Apps", "Discord, Telegram, WhatsApp, Signal"),
        "streaming": ("Streaming Platforms", "YouTube, Twitch, Kick, Vimeo"),
        "crypto": ("Crypto & Blockchain", "Coinbase, OpenSea, Binance, Rarible"),
        "shopping": ("Shopping & Marketplace", "eBay, Etsy, Amazon, Poshmark"),
        "other": ("Other Platforms", "Spotify, Patreon, Ko-fi, Last.fm"),
    }

    click.echo("\n📂 Platform Categories")
    click.echo("=" * 80)

    for cat_id, (name, examples) in categories_info.items():
        click.echo(f"\n🏷️  {name.upper()} ({cat_id})")
        click.echo(f"   Examples: {examples}")


@cli.command()
@click.argument("query", required=False)
@click.pass_context
def help(ctx, query):
    """❓ Show comprehensive help and documentation

    \b
    Displays help information for Nyx CLI. Can show general help or
    specific command help.

    \b
    EXAMPLES:

      # Show general help
      nyx-cli help

      # Show help for search command
      nyx-cli help search

      # Alternative syntax
      nyx-cli search --help
    """
    if query:
        # Show help for specific command
        cmd = cli.commands.get(query)
        if cmd:
            click.echo(cmd.get_help(ctx))
        else:
            click.echo(f"❌ Unknown command: {query}")
            click.echo("\n💡 Available commands:")
            for cmd_name in cli.commands:
                click.echo(f"   • {cmd_name}")
    else:
        # Show main help
        click.echo(cli.get_help(ctx))


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main CLI entry point."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        click.echo(f"\n❌ Fatal error: {e}", err=True)
        if "--debug" in sys.argv or "-d" in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
