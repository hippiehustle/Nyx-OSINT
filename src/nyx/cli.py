"""CLI entry point for Nyx OSINT application.

This module provides a comprehensive command-line interface for OSINT investigations,
including username searches across 200+ platforms, email intelligence gathering,
phone number lookups, and platform management.
"""

import asyncio
import logging
import pathlib
import sys
import traceback
from datetime import datetime

import click

from nyx import __version__
from nyx.config.base import load_config
from nyx.core.logger import get_logger, setup_logging
from nyx.intelligence.email import EmailIntelligence
from nyx.intelligence.phone import PhoneIntelligence
from nyx.intelligence.smart import SmartSearchInput, SmartSearchService
from nyx.models.platform import PlatformCategory
from nyx.osint.platforms import get_platform_database
from nyx.osint.search import SearchService

logger = get_logger(__name__)

# Configure logging for cleaner CLI output
logging.getLogger("nyx.osint.search").setLevel(logging.WARNING)


def _convert_config_value(value: str):
    """Convert string value to appropriate type for config.
    
    Args:
        value: String value to convert
        
    Returns:
        Converted value (bool, int, float, or str)
    """
    # Try boolean
    if value.lower() in ("true", "yes", "on", "1"):
        return True
    if value.lower() in ("false", "no", "off", "0"):
        return False
    
    # Try integer
    try:
        return int(value)
    except ValueError:
        pass
    
    # Try float
    try:
        return float(value)
    except ValueError:
        pass
    
    # Return as string
    return value


# ============================================================================
# Main CLI Group
# ============================================================================


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="nyx-cli")
@click.option(
    "-c",
    "--config",
    help="Path to configuration file",
    type=str,
    metavar="FILE",
)
@click.option("-d", "--debug", help="Enable debug logging", is_flag=True)
@click.pass_context
def cli(ctx, config, debug):
    """🔍 Nyx OSINT - Professional Intelligence Gathering Platform.

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
            click.echo(
                "💡 Run with a valid configuration or create default config files.",
                err=True,
            )
            sys.exit(1)
    elif ctx.invoked_subcommand is None and not ctx.resilient_parsing:
        # No subcommand provided, show help
        click.echo(ctx.get_help())


# ============================================================================
# Unified Search Command
# ============================================================================


@cli.command()
@click.option(
    "-u",
    "--username",
    help="Search for a username across platforms",
    metavar="USERNAME",
)
@click.option(
    "-e",
    "--email",
    help="Investigate an email address",
    metavar="EMAIL",
)
@click.option(
    "-p",
    "--phone",
    help="Investigate a phone number",
    metavar="PHONE",
)
@click.option(
    "-w",
    "--whois",
    help="Person lookup: 'FirstName LastName' or 'FirstName M LastName' (state optional with --region)",
    metavar="NAME",
)
@click.option(
    "-d",
    "--deep",
    help="Deep investigation: comprehensive search using all available methods",
    metavar="QUERY",
)
@click.option(
    "--profiles",
    is_flag=True,
    help="Search for online profiles associated with email (use with -e/--email)",
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
    type=click.Choice(
        [
            "social_media",
            "professional",
            "dating",
            "gaming",
            "forums",
            "adult",
            "blogging",
            "photography",
            "messaging",
            "streaming",
            "crypto",
            "shopping",
            "other",
        ],
        case_sensitive=False,
    ),
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
    "-t",
    "--timeout",
    type=int,
    default=120,
    help="Search timeout in seconds (default: 120)",
    metavar="SECONDS",
    show_default=True,
)
@click.option(
    "-o",
    "--output",
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
    "-v",
    "--verbose",
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
    whois,
    deep,
    profiles,
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
    if not (username or email or phone or whois or deep):
        click.echo("❌ Error: You must specify at least one search type:", err=True)
        click.echo("  -u/--username    Search for username", err=True)
        click.echo("  -e/--email       Investigate email", err=True)
        click.echo("  -p/--phone       Investigate phone", err=True)
        click.echo("  -w/--whois       Person lookup", err=True)
        click.echo("  -d/--deep        Deep investigation", err=True)
        click.echo("\n💡 Use 'nyx-cli search --help' for more information", err=True)
        sys.exit(1)

    if no_nsfw and only_nsfw:
        click.echo(
            "❌ Error: --no-nsfw and --only-nsfw are mutually exclusive",
            err=True,
        )
        sys.exit(1)

    if len([x for x in [username, email, phone, whois, deep] if x]) > 1:
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
            search_profiles=profiles,
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
    elif whois:
        _search_person(
            name=whois,
            state=region,
            output_format=output,
            save_file=save,
            verbose=verbose,
        )
    elif deep:
        _search_deep(
            query=deep,
            region=region,
            timeout=timeout,
            output_format=output,
            save_file=save,
            verbose=verbose,
        )


def _search_username(
    username: str,
    platforms_str: str | None,
    categories: tuple,
    exclude_nsfw: bool,
    only_nsfw: bool,
    timeout: int,
    output_format: str,
    save_file: str | None,
    verbose: bool,
):
    """Execute username search."""

    async def async_search() -> None:
        from nyx.core.utils import sanitize_username

        # Validate and sanitize username input
        sanitized_username = sanitize_username(username, min_length=1, max_length=255)
        if not sanitized_username:
            click.echo(f"❌ Invalid username: {username}", err=True)
            click.echo("   Username must be 1-255 characters and contain only alphanumeric, dash, underscore, or dot.", err=True)
            return

        # Enable debug logging if verbose mode
        if verbose:
            logging.getLogger("nyx.osint.checker").setLevel(logging.DEBUG)

        search_service = SearchService()

        # Parse platforms if provided
        platform_list = None
        if platforms_str:
            platform_list = [p.strip() for p in platforms_str.split(",") if p.strip()]

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
        progress_bar_ref = [None]  # Will hold reference to progress bar

        def show_progress(platform_name: str, status: str):
            """Show search progress and update progress bar."""
            if status == "checking":
                checked_count[0] += 1
            elif status == "found":
                found_count[0] += 1
            elif status == "cached":
                checked_count[0] += 1

            # Update progress bar if it exists
            if progress_bar_ref[0] and total_platforms[0] > 0:
                percentage = (checked_count[0] / total_platforms[0]) * 100.0
                progress_bar_ref[0].update("search", percentage)

        # Count total platforms that will be searched
        from nyx.osint.platforms import get_platform_database

        db = get_platform_database()
        platforms_dict = {}
        for name, platform in db.platforms.items():
            if not platform.is_active:
                continue
            if nsfw_filter and platform.is_nsfw:
                continue
            if platform_list and platform.name.lower() not in [
                p.lower() for p in platform_list
            ]:
                continue
            if category_list and platform.category.value not in [
                c.lower() for c in category_list
            ]:
                continue
            platforms_dict[name] = platform

        total_platforms[0] = len(platforms_dict)
        click.echo(f"🔎 Searching {total_platforms[0]} platforms...\n")

        # Create animated progress bar
        from nyx.utils.progress import AnimatedProgressBar, ProgressBarConfig

        # Configure progress bar
        progress_config = ProgressBarConfig(
            animation_sequence="░▒▓█▓▒",
            label_width=30,
            size_width=12,
            auto_fit=True,
            animation_speed=100,
            progress_update_interval=200,
        )

        progress_bar = AnimatedProgressBar(progress_config)
        progress_bar.add_item(
            "search",
            f"Searching {sanitized_username}",
            f"{total_platforms[0]} platforms",
            0.0,
        )

        # Store reference for callback
        progress_bar_ref[0] = progress_bar

        # Start animated progress bar
        progress_bar.start()

        try:
            results = await search_service.search_username(
                username=sanitized_username,
                platforms=platform_list,
                categories=category_list,
                exclude_nsfw=nsfw_filter,
                timeout=timeout,
                progress_callback=show_progress,
            )

            # Update progress bar to 100% when complete
            progress_bar.update("search", 100.0)
            # Give it a moment to show completion
            import time

            time.sleep(0.5)

        finally:
            # Stop progress bar and close HTTP resources
            progress_bar.stop()
            await search_service.aclose()

        # Add a newline after progress bar
        click.echo("")

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

            with pathlib.Path(save_file).open("w") as f:
                json.dump(results, f, indent=2)
            click.echo(f"\n💾 Results saved to: {save_file}")

    asyncio.run(async_search())


def _search_email(
    email: str,
    search_profiles: bool,
    timeout: int,
    output_format: str,
    save_file: str | None,
    verbose: bool,
):
    """Execute email search."""

    async def async_email_check():
        click.echo(f"📧 Investigating email: {email}")
        if search_profiles:
            click.echo("🔍 Profile search enabled (this may take longer)\n")
        else:
            click.echo("")

        email_intel = EmailIntelligence()
        result = await email_intel.investigate(email, search_profiles=search_profiles)

        if output_format == "json":
            import json

            click.echo(json.dumps(result.__dict__, indent=2, default=str))
        else:
            click.echo("=" * 80)
            click.echo("📊 Email Intelligence Report")
            click.echo("=" * 80)
            click.echo(f"\n📬 Address: {email}")
            click.echo(f"✅ Valid Format: {'Yes' if result.valid else 'No'}")
            click.echo(f"📮 Exists: {'Yes' if result.exists else 'Unknown'}")
            click.echo(f"🗑️  Disposable: {'Yes' if result.disposable else 'No'}")
            click.echo(f"🚨 Breached: {'Yes' if result.breached else 'No'}")

            if result.breached:
                click.echo("\n⚠️  BREACH INFORMATION:")
                click.echo(f"   Count: {result.breach_count}")
                if result.breaches:
                    click.echo(f"   Breaches: {', '.join(result.breaches)}")

            if result.providers:
                click.echo("\n🏢 ASSOCIATED PROVIDERS:")
                for provider in result.providers:
                    click.echo(f"   • {provider}")

            if result.online_profiles:
                click.echo(
                    f"\n🌐 ONLINE PROFILES ({len(result.online_profiles)} found):",
                )
                for platform, url in sorted(result.online_profiles.items()):
                    click.echo(f"   • {platform}: {url}")

            click.echo(f"\n⭐ Reputation Score: {result.reputation_score:.1f}/100")
            click.echo(f"🕐 Checked: {result.checked_at}")

        if save_file:
            import json

            with pathlib.Path(save_file).open("w") as f:
                json.dump(result.__dict__, f, indent=2, default=str)
            click.echo(f"\n💾 Results saved to: {save_file}")

    asyncio.run(async_email_check())


def _search_phone(
    phone: str,
    region: str | None,
    timeout: int,
    output_format: str,
    save_file: str | None,
    verbose: bool,
):
    """Execute phone search."""

    async def async_phone_check():
        from nyx.core.utils import validate_phone_number

        # Validate phone number format
        if not validate_phone_number(phone):
            click.echo(f"❌ Invalid phone number format: {phone}", err=True)
            click.echo("   Please provide a valid phone number (7-15 digits).", err=True)
            return

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
            click.echo("📊 Phone Intelligence Report")
            click.echo("=" * 80)
            click.echo(f"\n📞 Number: {phone}")
            click.echo(f"✅ Valid: {'Yes' if result.valid else 'No'}")

            if result.valid:
                click.echo("\n🌍 LOCATION:")
                click.echo(f"   Country: {result.country_name} ({result.country_code})")
                click.echo(f"   Location: {result.location or 'Unknown'}")
                click.echo(f"   Timezones: {', '.join(result.timezones)}")

                click.echo("\n📡 CARRIER:")
                click.echo(f"   Carrier: {result.carrier or 'Unknown'}")
                click.echo(f"   Line Type: {result.line_type}")

                click.echo("\n🔢 FORMATS:")
                click.echo(f"   International: {result.formatted_international}")
                click.echo(f"   National: {result.formatted_national}")
                click.echo(f"   E164: {result.formatted_e164}")

                click.echo(f"\n⭐ Reputation Score: {result.reputation_score:.1f}/100")

                if result.associated_name:
                    click.echo("\n👤 ASSOCIATED INFORMATION:")
                    click.echo(f"   Name: {result.associated_name}")

                if result.associated_addresses:
                    click.echo("   Addresses:")
                    for address in result.associated_addresses:
                        click.echo(f"     • {address}")

                if result.metadata.get("social_platforms"):
                    platforms = result.metadata["social_platforms"]
                    click.echo("\n🌐 SOCIAL PLATFORMS:")
                    for platform in platforms:
                        click.echo(f"   • {platform.title()}")

                if result.metadata.get("auto_detected_region"):
                    click.echo(
                        "\n💡 Region was auto-detected from phone number format",
                    )

            click.echo(f"\n🕐 Checked: {result.checked_at}")

        if save_file:
            import json

            with pathlib.Path(save_file).open("w") as f:
                json.dump(result.__dict__, f, indent=2, default=str)
            click.echo(f"\n💾 Results saved to: {save_file}")

    asyncio.run(async_phone_check())


def _search_person(
    name: str,
    state: str | None,
    output_format: str,
    save_file: str | None,
    verbose: bool,
):
    """Execute person WHOIS search."""

    async def async_person_check():
        from nyx.core.utils import sanitize_query

        # Validate and sanitize name
        sanitized_name = sanitize_query(name, max_length=200)
        if not sanitized_name:
            click.echo(f"❌ Invalid name: {name}", err=True)
            click.echo("   Name must be a valid string (max 200 characters).", err=True)
            return

        # Parse name
        parts = sanitized_name.strip().split()
        if len(parts) < 2:
            click.echo(
                "❌ Error: Name must include at least first and last name",
                err=True,
            )
            click.echo("   Examples: 'John Doe' or 'John M Doe'", err=True)
            return

        first_name = parts[0]
        last_name = parts[-1]
        middle_name = parts[1] if len(parts) == 3 else None

        full_name = " ".join(parts)
        click.echo(f"👤 Investigating person: {full_name}")
        if state:
            click.echo(f"📍 State: {state}")
        click.echo("")

        from nyx.intelligence.person import PersonIntelligence

        person_intel = PersonIntelligence()
        result = await person_intel.investigate(
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            state=state,
        )

        if output_format == "json":
            import json

            click.echo(json.dumps(result.__dict__, indent=2, default=str))
        else:
            click.echo("=" * 80)
            click.echo("📊 Person Intelligence Report")
            click.echo("=" * 80)
            click.echo(f"\n👤 NAME: {result.metadata['full_name']}")

            if result.age:
                click.echo(f"🎂 Age: {result.age}")
            elif result.age_range:
                click.echo(f"🎂 Age Range: {result.age_range}")

            if result.addresses:
                click.echo(f"\n🏠 ADDRESSES ({len(result.addresses)}):")
                for addr in result.addresses[:5]:  # Show first 5
                    click.echo(f"   • {addr}")

            if result.phone_numbers:
                click.echo(f"\n📱 PHONE NUMBERS ({len(result.phone_numbers)}):")
                for phone in result.phone_numbers[:5]:  # Show first 5
                    click.echo(f"   • {phone}")

            if result.email_addresses:
                click.echo(f"\n📧 EMAIL ADDRESSES ({len(result.email_addresses)}):")
                for email in result.email_addresses[:5]:  # Show first 5
                    click.echo(f"   • {email}")

            if result.relatives:
                click.echo(f"\n👨‍👩‍👧 POSSIBLE RELATIVES ({len(result.relatives)}):")
                for relative in result.relatives[:10]:  # Show first 10
                    click.echo(f"   • {relative}")

            if result.associates:
                click.echo(f"\n🤝 POSSIBLE ASSOCIATES ({len(result.associates)}):")
                for associate in result.associates[:10]:  # Show first 10
                    click.echo(f"   • {associate}")

            if result.social_profiles:
                click.echo(f"\n🌐 SOCIAL PROFILES ({len(result.social_profiles)}):")
                for platform, url in sorted(result.social_profiles.items())[:10]:
                    click.echo(f"   • {platform}: {url}")

            if result.employment:
                click.echo("\n💼 EMPLOYMENT/EDUCATION:")
                for item in result.employment[:5]:  # Show first 5
                    click.echo(f"   • {item}")

            click.echo(f"\n🕐 Checked: {result.checked_at}")

        if save_file:
            import json

            with pathlib.Path(save_file).open("w") as f:
                json.dump(result.__dict__, f, indent=2, default=str)
            click.echo(f"\n💾 Results saved to: {save_file}")

    asyncio.run(async_person_check())


def _search_deep(
    query: str,
    region: str | None,
    timeout: int,
    output_format: str,
    save_file: str | None,
    verbose: bool,
):
    """Execute deep investigation using centralized service."""

    async def async_deep_search():
        from nyx.core.utils import sanitize_query

        # Validate and sanitize query
        sanitized_query = sanitize_query(query, max_length=1000)
        if not sanitized_query:
            click.echo("❌ Invalid search query. Query must be a non-empty string (max 1000 characters).", err=True)
            return

        click.echo(f"🔎 Deep Investigation: {sanitized_query}")
        click.echo("🌊 Running comprehensive search across all available methods...")
        click.echo("")

        from nyx.intelligence.deep import DeepInvestigationService

        deep_service = DeepInvestigationService()
        try:
            result = await deep_service.investigate(
                query=sanitized_query,
                region=region,
                timeout=timeout,
                include_smart=True,
                include_web_search=True,
            )

            # Convert to legacy format for compatibility
            results = {
                "query": result.query,
                "username_results": result.username_results,
                "email_results": result.email_results,
                "phone_results": result.phone_results,
                "person_results": result.person_results,
                "timestamp": result.timestamp.isoformat(),
            }

            # Display progress
            click.echo("🔍 Searching as username...")
            if result.username_results:
                click.echo(
                    f"   ✓ Found {len(result.username_results)} username matches",
                )
            else:
                click.echo("   ✗ No username matches found")

            if result.email_results:
                click.echo("\n📧 Email investigation complete")
            if result.phone_results:
                click.echo("\n📱 Phone investigation complete")
            if result.person_results:
                click.echo("\n👤 Person investigation complete")
            if result.smart_results:
                click.echo("\n🧠 Smart search complete")

            # Display comprehensive results
            click.echo("\n" + "=" * 80)
            click.echo("📊 Deep Investigation Report")
            click.echo("=" * 80)

            if output_format == "json":
                import json

                # Convert dataclass results to dicts
                json_results = results.copy()
                if json_results.get("email_results"):
                    json_results["email_results"] = json_results["email_results"].__dict__
                if json_results.get("phone_results"):
                    json_results["phone_results"] = json_results["phone_results"].__dict__
                if json_results.get("person_results"):
                    json_results["person_results"] = json_results["person_results"].__dict__
                click.echo(json.dumps(json_results, indent=2, default=str))
            else:
                click.echo(f"\n🔍 Query: {sanitized_query}")

            if results["username_results"]:
                click.echo(
                    f"\n🌐 USERNAME MATCHES ({len(results['username_results'])}):",
                )
                for platform, data in sorted(results["username_results"].items())[:15]:
                    click.echo(f"   • {platform}: {data.get('url', '')}")

            if results.get("email_results"):
                email = results["email_results"]
                click.echo("\n📧 EMAIL INTELLIGENCE:")
                click.echo(f"   Valid: {email.valid}")
                click.echo(f"   Breached: {email.breached}")
                if email.online_profiles:
                    click.echo(f"   Online Profiles: {len(email.online_profiles)}")

            if results.get("phone_results"):
                phone = results["phone_results"]
                click.echo("\n📱 PHONE INTELLIGENCE:")
                click.echo(f"   Country: {phone.country_name}")
                click.echo(f"   Carrier: {phone.carrier or 'Unknown'}")
                click.echo(f"   Line Type: {phone.line_type}")
                if phone.associated_name:
                    click.echo(f"   Associated Name: {phone.associated_name}")

            if results.get("person_results"):
                person = results["person_results"]
                click.echo("\n👤 PERSON INTELLIGENCE:")
                click.echo(f"   Name: {person.metadata['full_name']}")
                if person.addresses:
                    click.echo(f"   Addresses Found: {len(person.addresses)}")
                if person.phone_numbers:
                    click.echo(f"   Phone Numbers Found: {len(person.phone_numbers)}")
                if person.social_profiles:
                    click.echo(
                        f"   Social Profiles Found: {len(person.social_profiles)}",
                    )

            total_findings = (
                len(results["username_results"])
                + (
                    1
                    if results.get("email_results") and results["email_results"].valid
                    else 0
                )
                + (
                    1
                    if results.get("phone_results") and results["phone_results"].valid
                    else 0
                )
                + (1 if results.get("person_results") else 0)
            )

            click.echo(f"\n✅ Total Findings: {total_findings}")
            click.echo(f"🕐 Completed: {datetime.now()}")

            if save_file:
                from nyx.core.utils import sanitize_file_path
                import json

                # Sanitize file path
                sanitized_path = sanitize_file_path(save_file)
                if sanitized_path:
                    try:
                        # Convert dataclass results to dicts for JSON serialization
                        save_data = results.copy()
                        if save_data.get("email_results"):
                            save_data["email_results"] = save_data["email_results"].__dict__
                        if save_data.get("phone_results"):
                            save_data["phone_results"] = save_data["phone_results"].__dict__
                        if save_data.get("person_results"):
                            save_data["person_results"] = save_data["person_results"].__dict__

                        with pathlib.Path(sanitized_path).open("w") as f:
                            json.dump(save_data, f, indent=2, default=str)
                        click.echo(f"\n💾 Results saved to: {sanitized_path}")
                    except Exception as e:
                        click.echo(f"❌ Failed to save results: {e}", err=True)
                else:
                    click.echo(f"❌ Invalid file path: {save_file}", err=True)
        finally:
            await deep_service.aclose()

    asyncio.run(async_deep_search())


# ============================================================================
# Platform Management Commands
# ============================================================================


@cli.command()
@click.option(
    "-c",
    "--category",
    multiple=True,
    help="Filter by category (can be used multiple times)",
    type=click.Choice(
        [
            "social_media",
            "professional",
            "dating",
            "gaming",
            "forums",
            "adult",
            "blogging",
            "photography",
            "messaging",
            "streaming",
            "crypto",
            "shopping",
            "other",
        ],
        case_sensitive=False,
    ),
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
    # Use platform database directly - no need for SearchService which would
    # create HTTP connections that we can't close in a synchronous function
    db = get_platform_database()
    
    # Calculate stats directly from platform database
    total = db.count_platforms()
    active = len([p for p in db.platforms.values() if p.is_active])
    nsfw = len(db.get_nsfw_platforms())
    
    stats_data = {
        "total_platforms": total,
        "active_platforms": active,
        "nsfw_platforms": nsfw,
        "sfw_platforms": active - nsfw,
    }

    click.echo("\n📊 Platform Statistics")
    click.echo("=" * 80)
    click.echo("\n📈 OVERVIEW:")
    click.echo(f"   Total Platforms: {stats_data['total_platforms']}")
    click.echo(f"   Active Platforms: {stats_data['active_platforms']}")
    click.echo(
        f"   Inactive Platforms: {stats_data['total_platforms'] - stats_data['active_platforms']}",
    )
    click.echo("\n🔞 CONTENT RATING:")
    click.echo(f"   NSFW Platforms: {stats_data['nsfw_platforms']}")
    click.echo(f"   SFW Platforms: {stats_data['sfw_platforms']}")

    if by_category:
        from collections import Counter

        categories = Counter(p.category.value for p in db.platforms.values())

        click.echo("\n📂 BY CATEGORY:")
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
        "social_media": (
            "Social Media",
            "Facebook, Twitter, Instagram, TikTok, Snapchat",
        ),
        "professional": (
            "Professional Networks",
            "LinkedIn, GitHub, Stack Overflow, AngelList",
        ),
        "dating": ("Dating Platforms", "Tinder, Bumble, OkCupid, Match, Hinge"),
        "gaming": (
            "Gaming Platforms",
            "Steam, Xbox Live, PlayStation, Roblox, Minecraft",
        ),
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


@cli.command()
@click.argument("text", nargs=-1, required=True)
@click.option(
    "--region",
    help="Region/state hint (e.g. US, CA, NY) to improve person/phone intelligence",
    metavar="CODE",
)
@click.option(
    "-o",
    "--output",
    type=click.Choice(["detailed", "json"], case_sensitive=False),
    default="detailed",
    show_default=True,
    help="Output format for Smart search results",
)
@click.option(
    "--save",
    type=click.Path(),
    help="Save Smart search result to file (JSON)",
    metavar="FILE",
)
@click.option(
    "--persist",
    is_flag=True,
    default=False,
    help="Persist results to database (creates/updates Target and TargetProfile records)",
)
@click.pass_context
def smart(ctx, text, region, output, save, persist):
    """🧠 Smart search from free-form target information.

    \b
    This command accepts any descriptive text you know about a target and:
      • Extracts usernames, emails, phone numbers, and names
      • Runs username/email/phone/person intelligence modules
      • Performs web search for additional context
      • Produces scored candidate profiles with confidence and reasoning
      • Optionally persists results to database for investigation tracking

    \b
    EXAMPLES:

      # Basic Smart search
      nyx-cli smart "John Doe from NY uses handle @johnny_d on social and email john@example.com"

      # With region hint
      nyx-cli smart "Jane Smith 415-555-2671" --region US

      # JSON output for tooling
      nyx-cli smart "user @redteam_analyst, email rt.analyst@company.com" -o json

      # Persist results to database
      nyx-cli smart "target info here" --persist
    """

    async def async_smart() -> None:
        free_text = " ".join(text)
        click.echo("🧠 Running Smart search...")
        click.echo("")

        smart_input = SmartSearchInput(raw_text=free_text, region=region)
        service = SmartSearchService()

        try:
            result = await service.smart_search(smart_input, persist_to_db=persist)
            
            if persist:
                click.echo("💾 Results persisted to database")
                click.echo("")

            if output == "json":
                import json

                # Convert results to a JSON-serializable structure
                data = {
                    "input": {
                        "raw_text": result.input.raw_text,
                        "region": result.input.region,
                    },
                    "identifiers": result.identifiers,
                    "candidates": [
                        {
                            "identifier": c.identifier,
                            "identifier_type": c.identifier_type,
                            "confidence": c.confidence,
                            "reason": c.reason,
                        }
                        for c in result.candidates
                    ],
                }
                click.echo(json.dumps(data, indent=2, default=str))
            else:
                # Human-readable detailed output with enhanced formatting
                click.echo("=" * 80)
                click.echo("🧠 SMART SEARCH RESULTS")
                click.echo("=" * 80)
                click.echo("")

                # Input summary
                click.echo("📝 Input:")
                click.echo(f"   Text: {result.input.raw_text[:100]}{'...' if len(result.input.raw_text) > 100 else ''}")
                if result.input.region:
                    click.echo(f"   Region: {result.input.region}")
                click.echo("")

                # Extracted identifiers
                click.echo("🔎 Extracted Identifiers:")
                ids = result.identifiers
                has_identifiers = False
                if ids["usernames"]:
                    click.echo(f"   👤 Usernames ({len(ids['usernames'])}): {', '.join(ids['usernames'][:5])}")
                    if len(ids['usernames']) > 5:
                        click.echo(f"      ... and {len(ids['usernames']) - 5} more")
                    has_identifiers = True
                if ids["emails"]:
                    click.echo(f"   📧 Emails ({len(ids['emails'])}): {', '.join(ids['emails'][:3])}")
                    if len(ids['emails']) > 3:
                        click.echo(f"      ... and {len(ids['emails']) - 3} more")
                    has_identifiers = True
                if ids["phones"]:
                    click.echo(f"   📱 Phones ({len(ids['phones'])}): {', '.join(ids['phones'][:3])}")
                    if len(ids['phones']) > 3:
                        click.echo(f"      ... and {len(ids['phones']) - 3} more")
                    has_identifiers = True
                if ids["names"]:
                    click.echo(f"   🆔 Names ({len(ids['names'])}): {', '.join(ids['names'][:3])}")
                    if len(ids['names']) > 3:
                        click.echo(f"      ... and {len(ids['names']) - 3} more")
                    has_identifiers = True
                
                if not has_identifiers:
                    click.echo("   ⚠️  No identifiers extracted from input")
                click.echo("")

                # Intelligence summary
                click.echo("📊 Intelligence Summary:")
                username_count = len(result.username_profiles)
                email_count = len(result.email_results)
                phone_count = len(result.phone_results)
                person_count = len(result.person_results)
                web_count = sum(len(v) for v in result.web_results.values())
                
                if username_count > 0:
                    total_platforms = sum(
                        len(p.get("platforms", {})) 
                        for p in result.username_profiles.values()
                    )
                    click.echo(f"   🌐 Username profiles: {username_count} username(s) on {total_platforms} platform(s)")
                if email_count > 0:
                    click.echo(f"   📧 Email intelligence: {email_count} email(s) analyzed")
                if phone_count > 0:
                    click.echo(f"   📱 Phone intelligence: {phone_count} phone(s) analyzed")
                if person_count > 0:
                    click.echo(f"   👤 Person records: {person_count} person(s) found")
                if web_count > 0:
                    click.echo(f"   🔍 Web search results: {web_count} result(s)")
                if username_count == 0 and email_count == 0 and phone_count == 0 and person_count == 0:
                    click.echo("   ⚠️  No intelligence data collected")
                click.echo("")

                # Candidates
                if not result.candidates:
                    click.echo("❌ No high-confidence candidates found")
                    click.echo("")
                else:
                    click.echo("=" * 80)
                    click.echo(f"✅ TOP CANDIDATES ({len(result.candidates)} total, showing top 10):")
                    click.echo("=" * 80)
                    click.echo("")
                    
                    for idx, cand in enumerate(result.candidates[:10], start=1):
                        pct = cand.confidence * 100.0
                        # Color coding based on confidence
                        if pct >= 80:
                            confidence_icon = "🟢"
                        elif pct >= 60:
                            confidence_icon = "🟡"
                        elif pct >= 40:
                            confidence_icon = "🟠"
                        else:
                            confidence_icon = "🔴"
                        
                        type_icons = {
                            "username": "👤",
                            "email": "📧",
                            "phone": "📱",
                            "name": "🆔",
                        }
                        type_icon = type_icons.get(cand.identifier_type, "🔍")
                        
                        click.echo(f"{confidence_icon} #{idx} [{pct:5.1f}%] {type_icon} {cand.identifier}")
                        click.echo(f"      Type: {cand.identifier_type.upper()}")
                        click.echo(f"      Reason: {cand.reason}")
                        
                        # Show additional data for high-confidence candidates
                        if pct >= 70 and isinstance(cand.data, dict):
                            data = cand.data
                            if cand.identifier_type == "username" and data.get("platforms"):
                                platforms = list(data["platforms"].keys())[:5]
                                click.echo(f"      Platforms: {', '.join(platforms)}")
                                if len(data["platforms"]) > 5:
                                    click.echo(f"      ... and {len(data['platforms']) - 5} more")
                            elif cand.identifier_type == "email" and data.get("online_profiles"):
                                profiles = list(data["online_profiles"].keys())[:3]
                                click.echo(f"      Online profiles: {', '.join(profiles)}")
                            elif cand.identifier_type == "phone" and data.get("carrier"):
                                click.echo(f"      Carrier: {data.get('carrier')}")
                                if data.get("line_type"):
                                    click.echo(f"      Line type: {data.get('line_type')}")
                        
                        click.echo("")
                    
                    if len(result.candidates) > 10:
                        click.echo(f"... and {len(result.candidates) - 10} more candidate(s) (use JSON output to see all)")
                        click.echo("")

            if save:
                import json

                save_data = {
                    "input": {
                        "raw_text": result.input.raw_text,
                        "region": result.input.region,
                    },
                    "identifiers": result.identifiers,
                    "candidates": [
                        {
                            "identifier": c.identifier,
                            "identifier_type": c.identifier_type,
                            "confidence": c.confidence,
                            "reason": c.reason,
                        }
                        for c in result.candidates
                    ],
                }

                with pathlib.Path(save).open("w", encoding="utf-8") as f:
                    json.dump(save_data, f, indent=2, default=str)

                click.echo(f"\n💾 Smart search result saved to: {save}")
        finally:
            await service.aclose()

    asyncio.run(async_smart())


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
            traceback.print_exc()
        sys.exit(1)


# ============================================================================
# Additional CLI Commands
# ============================================================================


@cli.command()
@click.option(
    "--list",
    "list_targets",
    is_flag=True,
    help="List all saved targets",
)
@click.option(
    "--create",
    help="Create a new target",
    metavar="NAME",
)
@click.option(
    "--category",
    help="Target category (person, organization, etc.)",
    metavar="CATEGORY",
)
@click.option(
    "--delete",
    help="Delete target by ID",
    metavar="ID",
)
@click.pass_context
def targets(ctx, list_targets, create, category, delete):
    """Manage investigation targets.

    \b
    EXAMPLES:

      # List all targets
      nyx-cli targets --list

      # Create a new target
      nyx-cli targets --create "John Doe" --category person

      # Delete a target
      nyx-cli targets --delete 1
    """
    try:
        import asyncio
        from nyx.core.database import ensure_database_initialized, get_database_manager
        from nyx.models.target import Target
        from sqlalchemy import select, delete as sql_delete

        async def async_targets():
            cfg = ctx.obj.get("config")
            db_manager = await ensure_database_initialized(cfg)
            async for session in db_manager.get_session():
                if list_targets:
                    stmt = select(Target).order_by(Target.last_searched.desc())
                    result = await session.execute(stmt)
                    targets_list = result.scalars().all()

                    if not targets_list:
                        click.echo("No targets found.")
                    else:
                        click.echo(f"\n📋 Targets ({len(targets_list)}):\n")
                        click.echo("=" * 80)
                        for target in targets_list:
                            click.echo(f"\nID: {target.id}")
                            click.echo(f"Name: {target.name}")
                            click.echo(f"Category: {target.category}")
                            click.echo(f"Last Searched: {target.last_searched or 'Never'}")
                            click.echo(f"Search Count: {target.search_count}")
                            click.echo("-" * 80)

                elif create:
                    target = Target(name=create, category=category or "person")
                    session.add(target)
                    await session.commit()
                    await session.refresh(target)
                    click.echo(f"✅ Created target: {target.name} (ID: {target.id})")

                elif delete:
                    stmt = sql_delete(Target).where(Target.id == int(delete))
                    await session.execute(stmt)
                    await session.commit()
                    click.echo(f"✅ Deleted target ID: {delete}")

                else:
                    click.echo(ctx.get_help())
                break

        asyncio.run(async_targets())
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if ctx.obj.get("debug"):
            import traceback
            traceback.print_exc()


@cli.command()
@click.option(
    "--target-id",
    help="Export results for specific target ID",
    metavar="ID",
    type=int,
)
@click.option(
    "--format",
    "export_format",
    type=click.Choice(["json", "html", "pdf", "csv"], case_sensitive=False),
    default="json",
    help="Export format",
)
@click.option(
    "--output",
    "-o",
    help="Output file path",
    metavar="FILE",
    required=True,
)
@click.pass_context
def export(ctx, target_id, export_format, output):
    """Export investigation results.

    \b
    EXAMPLES:

      # Export target results as JSON
      nyx-cli export --target-id 1 --format json -o results.json

      # Export as HTML report
      nyx-cli export --target-id 1 --format html -o report.html

      # Export as PDF
      nyx-cli export --target-id 1 --format pdf -o report.pdf
    """
    try:
        import asyncio
        from nyx.core.database import ensure_database_initialized, get_database_manager
        from nyx.core.utils import sanitize_file_path
        from nyx.models.target import Target, TargetProfile
        from sqlalchemy import select

        # Sanitize output path
        sanitized_path = sanitize_file_path(output)
        if not sanitized_path:
            click.echo(f"❌ Invalid file path: {output}", err=True)
            return

        async def async_export():
            cfg = ctx.obj.get("config")
            db_manager = await ensure_database_initialized(cfg)
            async for session in db_manager.get_session():
                if not target_id:
                    click.echo("❌ --target-id is required", err=True)
                    return

                # Get target and profiles
                stmt = select(Target).where(Target.id == target_id)
                result = await session.execute(stmt)
                target = result.scalar_one_or_none()

                if not target:
                    click.echo(f"❌ Target ID {target_id} not found", err=True)
                    return

                stmt = select(TargetProfile).where(TargetProfile.target_id == target_id)
                result = await session.execute(stmt)
                profiles = result.scalars().all()

                # Prepare export data
                export_data = {
                    "target": {
                        "id": target.id,
                        "name": target.name,
                        "category": target.category,
                        "description": target.description,
                    },
                    "profiles": [
                        {
                            "platform": p.platform,
                            "username": p.username,
                            "url": p.profile_url,
                            "confidence": p.confidence_score,
                        }
                        for p in profiles
                    ],
                }

                # Export based on format
                if export_format == "json":
                    import json
                    with open(sanitized_path, "w", encoding="utf-8") as f:
                        json.dump(export_data, f, indent=2, default=str)
                    click.echo(f"✅ Exported to {sanitized_path}")

                elif export_format == "html":
                    from nyx.export.html import HTMLExporter
                    exporter = HTMLExporter()
                    exporter.export(
                        {"profiles": export_data["profiles"]},
                        sanitized_path,
                        title=f"Investigation Report: {target.name}",
                    )
                    click.echo(f"✅ Exported to {sanitized_path}")

                elif export_format == "pdf":
                    from nyx.export.pdf import PDFExporter
                    exporter = PDFExporter()
                    exporter.export(
                        {"profiles": export_data["profiles"]},
                        sanitized_path,
                        title=f"Investigation Report: {target.name}",
                    )
                    click.echo(f"✅ Exported to {sanitized_path}")

                elif export_format == "csv":
                    from nyx.export.csv_export import CSVExporter
                    exporter = CSVExporter()
                    exporter.export(export_data["profiles"], sanitized_path)
                    click.echo(f"✅ Exported to {sanitized_path}")

                break

        asyncio.run(async_export())
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if ctx.obj.get("debug"):
            import traceback
            traceback.print_exc()


@cli.command()
@click.option(
    "--list",
    "list_history",
    is_flag=True,
    help="List search history",
)
@click.option(
    "--limit",
    default=50,
    help="Limit number of results",
    metavar="N",
    type=int,
)
@click.pass_context
def history(ctx, list_history, limit):
    """View search history.

    \b
    EXAMPLES:

      # List recent searches
      nyx-cli history --list

      # List last 20 searches
      nyx-cli history --list --limit 20
    """
    try:
        import asyncio
        from nyx.core.database import ensure_database_initialized, get_database_manager
        from nyx.models.target import SearchHistory
        from sqlalchemy import select

        async def async_history():
            cfg = ctx.obj.get("config")
            db_manager = await ensure_database_initialized(cfg)
            async for session in db_manager.get_session():
                stmt = select(SearchHistory).order_by(SearchHistory.timestamp.desc()).limit(limit)
                result = await session.execute(stmt)
                histories = result.scalars().all()

                if not histories:
                    click.echo("No search history found.")
                else:
                    click.echo(f"\n📜 Search History ({len(histories)}):\n")
                    click.echo("=" * 80)
                    for history in histories:
                        click.echo(f"\nID: {history.id}")
                        click.echo(f"Query: {history.search_query}")
                        click.echo(f"Type: {history.search_type}")
                        click.echo(f"Timestamp: {history.timestamp}")
                        click.echo(f"Platforms Searched: {history.platforms_searched}")
                        click.echo(f"Results Found: {history.results_found}")
                        click.echo(f"Duration: {history.duration_seconds:.2f}s")
                        click.echo("-" * 80)

                break

        asyncio.run(async_history())
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if ctx.obj.get("debug"):
            import traceback
            traceback.print_exc()


@cli.command()
@click.option(
    "--show",
    is_flag=True,
    help="Show current configuration",
)
@click.option(
    "--set",
    "set_key",
    help="Set configuration key (format: key=value)",
    metavar="KEY=VALUE",
)
@click.pass_context
def config(ctx, show, set_key):
    """Manage configuration.

    \b
    EXAMPLES:

      # Show current configuration
      nyx-cli config --show

      # Set a configuration value
      nyx-cli config --set http.timeout=30
    """
    if show:
        try:
            cfg = ctx.obj.get("config")
            if cfg:
                import json
                click.echo(json.dumps(cfg.model_dump(), indent=2, default=str))
            else:
                click.echo("No configuration loaded.")
        except Exception as e:
            click.echo(f"❌ Error: {e}", err=True)

    elif set_key:
        try:
            import yaml
            from pathlib import Path
            
            if "=" not in set_key:
                click.echo("❌ Invalid format. Use: key=value", err=True)
                click.echo("   Example: nyx-cli config --set http.timeout=30")
                return
            
            key, value = set_key.split("=", 1)
            key_parts = key.split(".")
            
            config_path = ctx.obj.get("config_path") or "config/settings.yaml"
            config_file = Path(config_path)
            
            if not config_file.exists():
                click.echo(f"❌ Config file not found: {config_file}", err=True)
                return
            
            # Load current config
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}
            
            # Navigate to nested key
            current = config_data
            for part in key_parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Set value (try to convert to appropriate type)
            final_key = key_parts[-1]
            converted_value = _convert_config_value(value)
            current[final_key] = converted_value
            
            # Save updated config
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            
            click.echo(f"✅ Set {key} = {converted_value}")
            
        except Exception as e:
            click.echo(f"❌ Error setting configuration: {e}", err=True)
            if ctx.obj.get("debug"):
                import traceback
                traceback.print_exc()
    else:
        click.echo(ctx.get_help())


@cli.group()
@click.pass_context
def update(ctx):
    """Update management commands.
    
    \b
    Check for, download, and install Nyx updates.
    """
    ctx.ensure_object(dict)


@update.command()
@click.pass_context
def check(ctx):
    """Check for available updates."""
    try:
        import asyncio
        from nyx.config.base import load_config
        from nyx.config.updater_config import UpdaterConfig
        from nyx.core.updater import UpdateChecker
        
        cfg = ctx.obj.get("config") or load_config(ctx.obj.get("config_path"))
        
        # Get updater config from main config or use defaults
        updater_config = UpdaterConfig(
            enabled=cfg.updater.enabled if hasattr(cfg, "updater") else True,
            source=getattr(cfg.updater, "source", "github") if hasattr(cfg, "updater") else "github",
            github_repo=getattr(cfg.updater, "github_repo", None) if hasattr(cfg, "updater") else None,
            custom_url=getattr(cfg.updater, "custom_url", None) if hasattr(cfg, "updater") else None,
            channel=getattr(cfg.updater, "channel", "stable") if hasattr(cfg, "updater") else "stable",
        )
        
        async def check_updates():
            checker = UpdateChecker(updater_config)
            update_info = await checker.check_for_updates()
            
            if update_info:
                click.echo(f"\n✅ Update available: {update_info['version']}")
                click.echo(f"   Current version: {update_info['current_version']}")
                if update_info.get("changelog"):
                    click.echo(f"\n📝 Changelog:\n{update_info['changelog']}")
                click.echo(f"\n💡 Run 'nyx-cli update download' to download the update")
            else:
                from nyx.core.version import get_current_version
                current = str(get_current_version())
                click.echo(f"\n✅ You are running the latest version: {current}")
        
        asyncio.run(check_updates())
    except ImportError:
        click.echo("⚠️  Update functionality not available in this build", err=True)
    except Exception as e:
        click.echo(f"❌ Error checking for updates: {e}", err=True)
        if ctx.obj.get("debug"):
            import traceback
            traceback.print_exc()


@update.command()
@click.option("--output", "-o", help="Output path for downloaded installer", type=click.Path())
@click.pass_context
def download(ctx, output):
    """Download available update."""
    try:
        import asyncio
        from pathlib import Path
        from nyx.config.base import load_config
        from nyx.config.updater_config import UpdaterConfig
        from nyx.core.updater import UpdateChecker, UpdateDownloader
        from nyx.utils.update_utils import add_update_history_entry, format_file_size
        
        cfg = ctx.obj.get("config") or load_config(ctx.obj.get("config_path"))
        
        # Get updater config
        updater_config = UpdaterConfig(
            enabled=cfg.updater.enabled if hasattr(cfg, "updater") else True,
            source=getattr(cfg.updater, "source", "github") if hasattr(cfg, "updater") else "github",
            github_repo=getattr(cfg.updater, "github_repo", None) if hasattr(cfg, "updater") else None,
            custom_url=getattr(cfg.updater, "custom_url", None) if hasattr(cfg, "updater") else None,
            channel=getattr(cfg.updater, "channel", "stable") if hasattr(cfg, "updater") else "stable",
        )
        
        async def download_update():
            # First check for updates
            checker = UpdateChecker(updater_config)
            update_info = await checker.check_for_updates()
            
            if not update_info:
                from nyx.core.version import get_current_version
                current = str(get_current_version())
                click.echo(f"✅ You are running the latest version: {current}")
                return
            
            click.echo(f"\n📥 Downloading update {update_info['version']}...")
            
            # Determine destination
            destination = None
            if output:
                destination = Path(output)
                destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Download with progress
            downloader = UpdateDownloader(updater_config)
            
            def progress_callback(downloaded: int, total: int):
                if total > 0:
                    percent = (downloaded / total) * 100
                    size_str = format_file_size(downloaded)
                    total_str = format_file_size(total)
                    click.echo(f"\r   Progress: {percent:.1f}% ({size_str} / {total_str})", nl=False)
            
            downloader.set_progress_callback(progress_callback)
            
            installer_path = await downloader.download_update(update_info, destination)
            
            if installer_path:
                click.echo(f"\n✅ Update downloaded successfully: {installer_path}")
                add_update_history_entry(
                    update_info['version'],
                    "download",
                    True,
                    {"path": str(installer_path)}
                )
                click.echo(f"\n💡 Run 'nyx-cli update install' to install the update")
            else:
                click.echo("\n❌ Download failed. Check logs for details.", err=True)
                add_update_history_entry(
                    update_info.get('version', 'unknown'),
                    "download",
                    False
                )
        
        asyncio.run(download_update())
    except ImportError:
        click.echo("⚠️  Update functionality not available in this build", err=True)
    except Exception as e:
        click.echo(f"❌ Error downloading update: {e}", err=True)
        if ctx.obj.get("debug"):
            import traceback
            traceback.print_exc()


@update.command()
@click.option("--installer", "-i", help="Path to installer file", type=click.Path(exists=True))
@click.option("--silent", "-s", is_flag=True, help="Install silently (no prompts)")
@click.pass_context
def install(ctx, installer, silent):
    """Install downloaded update."""
    try:
        import asyncio
        from pathlib import Path
        from nyx.config.base import load_config
        from nyx.config.updater_config import UpdaterConfig
        from nyx.core.updater import UpdateChecker, UpdateDownloader, UpdateInstaller
        from nyx.utils.update_utils import add_update_history_entry
        
        cfg = ctx.obj.get("config") or load_config(ctx.obj.get("config_path"))
        
        # Get updater config
        updater_config = UpdaterConfig(
            enabled=cfg.updater.enabled if hasattr(cfg, "updater") else True,
            source=getattr(cfg.updater, "source", "github") if hasattr(cfg, "updater") else "github",
            github_repo=getattr(cfg.updater, "github_repo", None) if hasattr(cfg, "updater") else None,
            custom_url=getattr(cfg.updater, "custom_url", None) if hasattr(cfg, "updater") else None,
            channel=getattr(cfg.updater, "channel", "stable") if hasattr(cfg, "updater") else "stable",
        )
        
        async def install_update():
            installer_path = None
            
            if installer:
                installer_path = Path(installer)
            else:
                # Try to find downloaded installer
                import tempfile
                temp_dir = Path(tempfile.gettempdir()) / "Nyx" / "updates"
                if temp_dir.exists():
                    # Find latest .exe file
                    exe_files = list(temp_dir.glob("*.exe"))
                    if exe_files:
                        installer_path = max(exe_files, key=lambda p: p.stat().st_mtime)
            
            if not installer_path or not installer_path.exists():
                click.echo("❌ No installer found. Please download an update first:", err=True)
                click.echo("   nyx-cli update download")
                click.echo("   Or specify installer path: nyx-cli update install --installer <path>")
                return
            
            # Confirm installation
            if not silent:
                click.echo(f"\n⚠️  This will install update from: {installer_path}")
                if not click.confirm("Do you want to continue?"):
                    click.echo("Installation cancelled.")
                    return
            
            click.echo(f"\n🔧 Installing update from {installer_path}...")
            
            installer_obj = UpdateInstaller(updater_config)
            success = await installer_obj.install_update(installer_path, silent=silent)
            
            if success:
                click.echo("✅ Update installed successfully!")
                add_update_history_entry(
                    installer_path.stem,  # Use filename as version identifier
                    "install",
                    True,
                    {"path": str(installer_path)}
                )
                click.echo("\n💡 Please restart the application to use the new version.")
            else:
                click.echo("❌ Installation failed. Check logs for details.", err=True)
                add_update_history_entry(
                    installer_path.stem,
                    "install",
                    False
                )
        
        asyncio.run(install_update())
    except ImportError:
        click.echo("⚠️  Update functionality not available in this build", err=True)
    except Exception as e:
        click.echo(f"❌ Error installing update: {e}", err=True)
        if ctx.obj.get("debug"):
            import traceback
            traceback.print_exc()


@update.command()
@click.pass_context
def status(ctx):
    """Show update status."""
    try:
        from nyx.core.version import get_current_version
        from nyx.utils.update_utils import get_last_update_check, get_last_installed_version
        
        current = str(get_current_version())
        click.echo(f"Current version: {current}")
        
        last_check = get_last_update_check()
        if last_check:
            click.echo(f"Last check: {last_check}")
        else:
            click.echo("Last check: Never")
        
        last_installed = get_last_installed_version()
        if last_installed:
            click.echo(f"Last installed: {last_installed}")
    except ImportError:
        click.echo("⚠️  Update functionality not available in this build", err=True)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


@update.command()
@click.option("--enabled/--disabled", help="Enable or disable auto-updater")
@click.option("--source", type=click.Choice(["github", "custom", "disabled"]), help="Update source")
@click.option("--github-repo", help="GitHub repository (owner/repo)")
@click.option("--custom-url", help="Custom update server URL")
@click.option("--check-on-startup/--no-check-on-startup", help="Check for updates on startup")
@click.option("--frequency", type=click.Choice(["on_startup", "daily", "weekly", "manual_only"]), help="Check frequency")
@click.option("--auto-download/--no-auto-download", help="Automatically download updates")
@click.option("--auto-install/--no-auto-install", help="Automatically install updates")
@click.option("--channel", type=click.Choice(["stable", "beta", "alpha"]), help="Update channel")
@click.pass_context
def settings(ctx, enabled, source, github_repo, custom_url, check_on_startup, frequency, auto_download, auto_install, channel):
    """Configure update settings."""
    try:
        from nyx.config.base import load_config, Config
        import yaml
        from pathlib import Path
        
        cfg = ctx.obj.get("config") or load_config(ctx.obj.get("config_path"))
        config_path = ctx.obj.get("config_path") or "config/settings.yaml"
        config_file = Path(config_path)
        
        if not config_file.exists():
            click.echo(f"❌ Config file not found: {config_file}", err=True)
            return
        
        # Load current config
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}
        
        # Initialize updater section if needed
        if "updater" not in config_data:
            config_data["updater"] = {}
        
        updater = config_data["updater"]
        
        # Update values if provided
        if enabled is not None:
            updater["enabled"] = enabled
        if source:
            updater["source"] = source
        if github_repo is not None:
            updater["github_repo"] = github_repo if github_repo else None
        if custom_url is not None:
            updater["custom_url"] = custom_url if custom_url else None
        if check_on_startup is not None:
            updater["check_on_startup"] = check_on_startup
        if frequency:
            updater["check_frequency"] = frequency
        if auto_download is not None:
            updater["auto_download"] = auto_download
        if auto_install is not None:
            updater["auto_install"] = auto_install
        if channel:
            updater["channel"] = channel
        
        # Save updated config
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        click.echo("✅ Update settings saved successfully!")
        click.echo(f"\nCurrent settings:")
        click.echo(f"  Enabled: {updater.get('enabled', True)}")
        click.echo(f"  Source: {updater.get('source', 'github')}")
        click.echo(f"  GitHub Repo: {updater.get('github_repo', 'None')}")
        click.echo(f"  Custom URL: {updater.get('custom_url', 'None')}")
        click.echo(f"  Check on Startup: {updater.get('check_on_startup', True)}")
        click.echo(f"  Frequency: {updater.get('check_frequency', 'daily')}")
        click.echo(f"  Auto Download: {updater.get('auto_download', False)}")
        click.echo(f"  Auto Install: {updater.get('auto_install', False)}")
        click.echo(f"  Channel: {updater.get('channel', 'stable')}")
        
    except ImportError:
        click.echo("⚠️  Update functionality not available in this build", err=True)
    except Exception as e:
        click.echo(f"❌ Error configuring settings: {e}", err=True)
        if ctx.obj.get("debug"):
            import traceback
            traceback.print_exc()


@update.command()
@click.argument("version")
@click.option("--remove", "-r", is_flag=True, help="Remove version from skip list")
@click.pass_context
def skip(ctx, version, remove):
    """Skip a specific version from updates."""
    try:
        from nyx.config.base import load_config
        import yaml
        from pathlib import Path
        
        cfg = ctx.obj.get("config") or load_config(ctx.obj.get("config_path"))
        config_path = ctx.obj.get("config_path") or "config/settings.yaml"
        config_file = Path(config_path)
        
        if not config_file.exists():
            click.echo(f"❌ Config file not found: {config_file}", err=True)
            return
        
        # Load current config
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}
        
        # Initialize updater section if needed
        if "updater" not in config_data:
            config_data["updater"] = {}
        
        updater = config_data["updater"]
        
        # Initialize skip_versions if needed
        if "skip_versions" not in updater:
            updater["skip_versions"] = []
        
        skip_versions = updater["skip_versions"]
        
        if remove:
            if version in skip_versions:
                skip_versions.remove(version)
                click.echo(f"✅ Removed {version} from skip list")
            else:
                click.echo(f"⚠️  Version {version} is not in skip list")
        else:
            if version not in skip_versions:
                skip_versions.append(version)
                click.echo(f"✅ Added {version} to skip list")
            else:
                click.echo(f"⚠️  Version {version} is already in skip list")
        
        updater["skip_versions"] = skip_versions
        
        # Save updated config
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        click.echo(f"\nSkipped versions: {', '.join(skip_versions) if skip_versions else 'None'}")
        
    except ImportError:
        click.echo("⚠️  Update functionality not available in this build", err=True)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if ctx.obj.get("debug"):
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
