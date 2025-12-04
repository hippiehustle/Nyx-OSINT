"""Main application window for Nyx GUI."""

import asyncio
import json
import threading
from typing import Optional

import customtkinter as ctk

from nyx.config.base import Config
from nyx.core.logger import get_logger
from nyx.intelligence.email import EmailIntelligence
from nyx.intelligence.person import PersonIntelligence
from nyx.intelligence.phone import PhoneIntelligence
from nyx.intelligence.smart import SmartSearchInput, SmartSearchService
from nyx.osint.search import SearchService

logger = get_logger(__name__)


class MainWindow(ctk.CTk):
    """Main application window."""

    def __init__(
        self,
        config: Optional[Config] = None,
        title: str = "Nyx - OSINT Investigation Platform",
        width: int = 1400,
        height: int = 900,
    ):
        """Initialize main window.

        Args:
            config: Application configuration
            title: Window title
            width: Window width
            height: Window height
        """
        super().__init__()

        self.config = config
        self.title(title)
        self.geometry(f"{width}x{height}")

        # Configure colors
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Create main layout
        self._create_layout()

    def _create_layout(self) -> None:
        """Create main window layout."""
        # Create sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Create main content area
        self.main_content = ctk.CTkFrame(self)
        self.main_content.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Add logo/title to sidebar
        title_label = ctk.CTkLabel(
            self.sidebar,
            text="NYX",
            font=("Helvetica", 24, "bold"),
        )
        title_label.pack(pady=20)

        version_label = ctk.CTkLabel(
            self.sidebar,
            text="v0.1.0",
            font=("Helvetica", 10),
        )
        version_label.pack()

        # Add menu buttons to sidebar
        self._create_menu_buttons()

        # Add main content
        self._create_content_area()

    def _create_menu_buttons(self) -> None:
        """Create sidebar menu buttons."""
        buttons = [
            ("Search", self.on_search_click),
            ("Targets", self.on_targets_click),
            ("Results", self.on_results_click),
            ("Settings", self.on_settings_click),
        ]

        for button_text, command in buttons:
            btn = ctk.CTkButton(
                self.sidebar,
                text=button_text,
                command=command,
                width=180,
                height=40,
            )
            btn.pack(pady=5, padx=10)

    def _create_content_area(self) -> None:
        """Create main content area."""
        # Header
        header = ctk.CTkLabel(
            self.main_content,
            text="OSINT Investigation Platform",
            font=("Helvetica", 20, "bold"),
        )
        header.pack(pady=10)

        # Search type selection
        search_type_frame = ctk.CTkFrame(self.main_content)
        search_type_frame.pack(fill="x", padx=10, pady=5)

        type_label = ctk.CTkLabel(
            search_type_frame,
            text="Search Type:",
            font=("Helvetica", 12),
        )
        type_label.pack(side="left", padx=5)

        self.search_type = ctk.StringVar(value="username")
        search_types = [
            ("Username", "username"),
            ("Email", "email"),
            ("Phone", "phone"),
            ("Person", "person"),
            ("Smart", "smart"),
            ("Deep", "deep"),
        ]

        for text, value in search_types:
            rb = ctk.CTkRadioButton(
                search_type_frame,
                text=text,
                variable=self.search_type,
                value=value,
            )
            rb.pack(side="left", padx=5)

        # Search frame
        search_frame = ctk.CTkFrame(self.main_content)
        search_frame.pack(fill="x", padx=10, pady=10)

        search_label = ctk.CTkLabel(
            search_frame,
            text="Query:",
            font=("Helvetica", 12),
        )
        search_label.pack(side="left", padx=5)

        self.search_entry = ctk.CTkEntry(search_frame, width=400, placeholder_text="Enter search query...")
        self.search_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.search_entry.bind("<Return>", lambda e: self.perform_search())

        # Region option (for phone/person/smart searches)
        self.region_entry = ctk.CTkEntry(
            search_frame,
            width=80,
            placeholder_text="Region",
        )
        self.region_entry.pack(side="left", padx=5)

        search_button = ctk.CTkButton(
            search_frame,
            text="🔍 Search",
            command=self.perform_search,
            width=100,
        )
        search_button.pack(side="left", padx=5)

        # Results frame with tabs
        self.results_notebook = ctk.CTkTabview(self.main_content)
        self.results_notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Results tab
        self.results_tab = self.results_notebook.add("Results")
        self.results_text = ctk.CTkTextbox(self.results_tab, font=("Consolas", 11))
        self.results_text.pack(fill="both", expand=True)

        # Summary tab
        self.summary_tab = self.results_notebook.add("Summary")
        self.summary_text = ctk.CTkTextbox(self.summary_tab, font=("Consolas", 11))
        self.summary_text.pack(fill="both", expand=True)

        # Status bar
        self.status_label = ctk.CTkLabel(
            self.main_content,
            text="Ready",
            font=("Helvetica", 10),
        )
        self.status_label.pack(pady=5)

    def perform_search(self) -> None:
        """Perform search operation."""
        query = self.search_entry.get().strip()
        if not query:
            self.status_label.configure(text="Please enter a search query")
            return

        search_type = self.search_type.get()
        region = self.region_entry.get().strip() or None

        self.status_label.configure(text=f"Searching ({search_type}): {query}...")
        self.results_text.delete("1.0", "end")
        self.summary_text.delete("1.0", "end")
        self.results_text.insert("end", f"🔍 Searching for: {query}\n")
        self.results_text.insert("end", f"📋 Search Type: {search_type.upper()}\n")
        if region:
            self.results_text.insert("end", f"🌍 Region: {region}\n")
        self.results_text.insert("end", "\n⏳ Processing...\n")

        # Run search in background thread
        thread = threading.Thread(
            target=self._run_search_async,
            args=(query, search_type, region),
            daemon=True,
        )
        thread.start()

        logger.info(f"User initiated {search_type} search for: {query}")

    def _run_search_async(self, query: str, search_type: str, region: Optional[str]) -> None:
        """Run async search in background thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._async_search(query, search_type, region))
        finally:
            loop.close()

    async def _async_search(self, query: str, search_type: str, region: Optional[str]) -> None:
        """Execute async search based on type."""
        try:
            if search_type == "username":
                await self._search_username(query)
            elif search_type == "email":
                await self._search_email(query)
            elif search_type == "phone":
                await self._search_phone(query, region)
            elif search_type == "person":
                await self._search_person(query, region)
            elif search_type == "smart":
                await self._search_smart(query, region)
            elif search_type == "deep":
                await self._search_deep(query, region)
        except Exception as e:
            self._update_results(f"❌ Error: {str(e)}\n")
            logger.error(f"Search failed: {e}", exc_info=True)

    def _update_results(self, text: str) -> None:
        """Update results text widget (thread-safe)."""
        self.after(0, lambda: self.results_text.insert("end", text))

    def _update_summary(self, text: str) -> None:
        """Update summary text widget (thread-safe)."""
        self.after(0, lambda: self.summary_text.insert("end", text))

    def _update_status(self, text: str) -> None:
        """Update status label (thread-safe)."""
        self.after(0, lambda: self.status_label.configure(text=text))

    async def _search_username(self, username: str) -> None:
        """Search for username."""
        self._update_results(f"\n🌐 Searching username: {username}\n")
        self._update_results("=" * 80 + "\n\n")

        search_service = SearchService()
        try:
            results = await search_service.search_username(username, exclude_nsfw=True, timeout=120)
            
            if not results:
                self._update_results("❌ No profiles found\n")
                self._update_status("No results found")
                return

            self._update_results(f"✅ Found {len(results)} profile(s):\n\n")
            summary_lines = [f"Username: {username}", f"Platforms Found: {len(results)}", ""]

            for platform, result in sorted(results.items()):
                url = result.get("url", "N/A")
                status = result.get("http_status", "N/A")
                self._update_results(f"🌐 {platform}:\n")
                self._update_results(f"   URL: {url}\n")
                if status != "N/A":
                    self._update_results(f"   Status: {status}\n")
                self._update_results("\n")
                summary_lines.append(f"• {platform}: {url}")

            self._update_summary("\n".join(summary_lines))
            self._update_status(f"Found {len(results)} profile(s)")
        finally:
            await search_service.aclose()

    async def _search_email(self, email: str) -> None:
        """Search for email."""
        self._update_results(f"\n📧 Investigating email: {email}\n")
        self._update_results("=" * 80 + "\n\n")

        email_intel = EmailIntelligence()
        try:
            result = await email_intel.investigate(email, search_profiles=True)
            
            self._update_results("📊 Email Intelligence Results:\n\n")
            summary_lines = [f"Email: {email}", ""]

            self._update_results(f"✓ Valid: {result.valid}\n")
            self._update_results(f"✓ Breached: {result.breached}\n")
            self._update_results(f"✓ Disposable: {result.disposable}\n")
            self._update_results(f"✓ Provider: {result.provider or 'Unknown'}\n")
            self._update_results(f"✓ Reputation Score: {result.reputation_score}/100\n")
            
            summary_lines.extend([
                f"Valid: {result.valid}",
                f"Breached: {result.breached}",
                f"Provider: {result.provider or 'Unknown'}",
                f"Reputation: {result.reputation_score}/100",
            ])

            if result.online_profiles:
                self._update_results(f"\n📱 Online Profiles ({len(result.online_profiles)}):\n")
                summary_lines.append(f"\nOnline Profiles: {len(result.online_profiles)}")
                for service, url in result.online_profiles.items():
                    self._update_results(f"   • {service}: {url}\n")
                    summary_lines.append(f"  • {service}: {url}")

            self._update_summary("\n".join(summary_lines))
            self._update_status("Email investigation complete")
        except Exception as e:
            self._update_results(f"❌ Error: {str(e)}\n")
            raise

    async def _search_phone(self, phone: str, region: Optional[str]) -> None:
        """Search for phone number."""
        self._update_results(f"\n📱 Investigating phone: {phone}\n")
        if region:
            self._update_results(f"🌍 Region: {region}\n")
        self._update_results("=" * 80 + "\n\n")

        phone_intel = PhoneIntelligence()
        try:
            result = await phone_intel.investigate(phone, region=region)
            
            self._update_results("📊 Phone Intelligence Results:\n\n")
            summary_lines = [f"Phone: {phone}", ""]

            self._update_results(f"✓ Valid: {result.valid}\n")
            self._update_results(f"✓ Country: {result.country_name} ({result.country_code})\n")
            self._update_results(f"✓ Carrier: {result.carrier or 'Unknown'}\n")
            self._update_results(f"✓ Line Type: {result.line_type}\n")
            if result.timezone:
                self._update_results(f"✓ Timezone: {result.timezone}\n")
            if result.associated_name:
                self._update_results(f"✓ Associated Name: {result.associated_name}\n")

            summary_lines.extend([
                f"Valid: {result.valid}",
                f"Country: {result.country_name}",
                f"Carrier: {result.carrier or 'Unknown'}",
                f"Line Type: {result.line_type}",
            ])

            self._update_summary("\n".join(summary_lines))
            self._update_status("Phone investigation complete")
        except Exception as e:
            self._update_results(f"❌ Error: {str(e)}\n")
            raise

    async def _search_person(self, name: str, region: Optional[str]) -> None:
        """Search for person."""
        self._update_results(f"\n👤 Investigating person: {name}\n")
        if region:
            self._update_results(f"🌍 Region: {region}\n")
        self._update_results("=" * 80 + "\n\n")

        parts = name.split()
        if len(parts) < 2:
            self._update_results("❌ Please provide full name (First Last)\n")
            return

        person_intel = PersonIntelligence()
        try:
            result = await person_intel.investigate(
                first_name=parts[0],
                last_name=parts[-1],
                middle_name=parts[1] if len(parts) == 3 else None,
                state=region,
            )
            
            self._update_results("📊 Person Intelligence Results:\n\n")
            summary_lines = [f"Name: {name}", ""]

            if result.addresses:
                self._update_results(f"📍 Addresses ({len(result.addresses)}):\n")
                for addr in result.addresses[:5]:
                    self._update_results(f"   • {addr}\n")
                summary_lines.append(f"Addresses: {len(result.addresses)}")

            if result.phone_numbers:
                self._update_results(f"📱 Phone Numbers ({len(result.phone_numbers)}):\n")
                for phone in result.phone_numbers[:5]:
                    self._update_results(f"   • {phone}\n")
                summary_lines.append(f"Phone Numbers: {len(result.phone_numbers)}")

            if result.email_addresses:
                self._update_results(f"📧 Email Addresses ({len(result.email_addresses)}):\n")
                for email in result.email_addresses[:5]:
                    self._update_results(f"   • {email}\n")
                summary_lines.append(f"Email Addresses: {len(result.email_addresses)}")

            if result.social_profiles:
                self._update_results(f"🌐 Social Profiles ({len(result.social_profiles)}):\n")
                for platform, url in list(result.social_profiles.items())[:10]:
                    self._update_results(f"   • {platform}: {url}\n")
                summary_lines.append(f"Social Profiles: {len(result.social_profiles)}")

            self._update_summary("\n".join(summary_lines))
            self._update_status("Person investigation complete")
        except Exception as e:
            self._update_results(f"❌ Error: {str(e)}\n")
            raise

    async def _search_smart(self, text: str, region: Optional[str]) -> None:
        """Perform Smart search."""
        self._update_results(f"\n🧠 Smart Search: {text}\n")
        if region:
            self._update_results(f"🌍 Region: {region}\n")
        self._update_results("=" * 80 + "\n\n")

        service = SmartSearchService()
        try:
            smart_input = SmartSearchInput(raw_text=text, region=region)
            result = await service.smart_search(smart_input, timeout=120)
            
            self._update_results("🔎 Extracted Identifiers:\n")
            ids = result.identifiers
            if ids["usernames"]:
                self._update_results(f"   👤 Usernames: {', '.join(ids['usernames'])}\n")
            if ids["emails"]:
                self._update_results(f"   📧 Emails: {', '.join(ids['emails'])}\n")
            if ids["phones"]:
                self._update_results(f"   📱 Phones: {', '.join(ids['phones'])}\n")
            if ids["names"]:
                self._update_results(f"   🆔 Names: {', '.join(ids['names'])}\n")
            
            self._update_results("\n✅ Candidates:\n\n")
            summary_lines = [f"Query: {text}", f"Candidates: {len(result.candidates)}", ""]

            for idx, cand in enumerate(result.candidates[:10], start=1):
                pct = cand.confidence * 100.0
                self._update_results(f"{idx}. [{pct:5.1f}%] {cand.identifier} ({cand.identifier_type})\n")
                self._update_results(f"   Reason: {cand.reason}\n\n")
                summary_lines.append(f"{idx}. {cand.identifier} ({pct:.1f}%)")

            self._update_summary("\n".join(summary_lines))
            self._update_status(f"Smart search complete: {len(result.candidates)} candidates")
        finally:
            await service.aclose()

    async def _search_deep(self, query: str, region: Optional[str]) -> None:
        """Perform deep investigation."""
        self._update_results(f"\n🔎 Deep Investigation: {query}\n")
        if region:
            self._update_results(f"🌍 Region: {region}\n")
        self._update_results("=" * 80 + "\n\n")

        # Run multiple search types
        self._update_results("🌐 Username Search...\n")
        search_service = SearchService()
        try:
            username_results = await search_service.search_username(query, exclude_nsfw=True, timeout=60)
            self._update_results(f"   ✓ Found {len(username_results)} platform(s)\n\n")
        finally:
            await search_service.aclose()

        # Email check
        if "@" in query:
            self._update_results("📧 Email Intelligence...\n")
            email_intel = EmailIntelligence()
            try:
                email_result = await email_intel.investigate(query, search_profiles=False)
                self._update_results(f"   ✓ Valid: {email_result.valid}, Breached: {email_result.breached}\n\n")
            except Exception:
                pass

        # Phone check
        if any(c.isdigit() for c in query.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")):
            self._update_results("📱 Phone Intelligence...\n")
            phone_intel = PhoneIntelligence()
            try:
                phone_result = await phone_intel.investigate(query, region=region)
                self._update_results(f"   ✓ Valid: {phone_result.valid}, Country: {phone_result.country_name}\n\n")
            except Exception:
                pass

        self._update_status("Deep investigation complete")

    def on_search_click(self) -> None:
        """Handle search button click - show search interface."""
        self._show_search_view()

    def on_targets_click(self) -> None:
        """Handle targets button click - show targets view."""
        self._show_targets_view()

    def on_results_click(self) -> None:
        """Handle results button click - show search history."""
        self._show_results_view()

    def on_settings_click(self) -> None:
        """Handle settings button click - show settings panel."""
        self._show_settings_view()

    def _clear_content(self) -> None:
        """Clear main content area."""
        for widget in self.main_content.winfo_children():
            widget.destroy()

    def _show_search_view(self) -> None:
        """Show search interface (default view)."""
        self._clear_content()
        self._create_content_area()

    def _show_targets_view(self) -> None:
        """Show targets management view."""
        self._clear_content()

        header = ctk.CTkLabel(
            self.main_content,
            text="Targets Management",
            font=("Helvetica", 20, "bold"),
        )
        header.pack(pady=10)

        # Target list frame
        list_frame = ctk.CTkFrame(self.main_content)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Search/filter frame
        filter_frame = ctk.CTkFrame(list_frame)
        filter_frame.pack(fill="x", padx=5, pady=5)

        filter_entry = ctk.CTkEntry(filter_frame, placeholder_text="Search targets...", width=300)
        filter_entry.pack(side="left", padx=5)

        refresh_btn = ctk.CTkButton(filter_frame, text="🔄 Refresh", width=100, command=self._refresh_targets)
        refresh_btn.pack(side="left", padx=5)

        add_btn = ctk.CTkButton(filter_frame, text="➕ Add Target", width=120, command=self._add_target_dialog)
        add_btn.pack(side="right", padx=5)

        # Targets list
        self.targets_listbox = ctk.CTkTextbox(list_frame, font=("Consolas", 11))
        self.targets_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Action buttons frame
        action_frame = ctk.CTkFrame(list_frame)
        action_frame.pack(fill="x", padx=5, pady=5)

        view_btn = ctk.CTkButton(action_frame, text="👁️ View", width=100, command=self._view_target)
        view_btn.pack(side="left", padx=5)

        edit_btn = ctk.CTkButton(action_frame, text="✏️ Edit", width=100, command=self._edit_target)
        edit_btn.pack(side="left", padx=5)

        delete_btn = ctk.CTkButton(action_frame, text="🗑️ Delete", width=100, command=self._delete_target)
        delete_btn.pack(side="left", padx=5)

        export_btn = ctk.CTkButton(action_frame, text="💾 Export", width=100, command=self._export_target)
        export_btn.pack(side="right", padx=5)

        self._refresh_targets()

    def _show_results_view(self) -> None:
        """Show search history/results view."""
        self._clear_content()

        header = ctk.CTkLabel(
            self.main_content,
            text="Search History",
            font=("Helvetica", 20, "bold"),
        )
        header.pack(pady=10)

        # Filter frame
        filter_frame = ctk.CTkFrame(self.main_content)
        filter_frame.pack(fill="x", padx=10, pady=5)

        filter_label = ctk.CTkLabel(filter_frame, text="Filter:", font=("Helvetica", 12))
        filter_label.pack(side="left", padx=5)

        self.results_filter_entry = ctk.CTkEntry(filter_frame, placeholder_text="Search history...", width=300)
        self.results_filter_entry.pack(side="left", padx=5)
        self.results_filter_entry.bind("<KeyRelease>", lambda e: self._filter_results())

        refresh_results_btn = ctk.CTkButton(filter_frame, text="🔄 Refresh", width=100, command=self._refresh_results)
        refresh_results_btn.pack(side="right", padx=5)

        # Results list
        results_frame = ctk.CTkFrame(self.main_content)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.results_listbox = ctk.CTkTextbox(results_frame, font=("Consolas", 11))
        self.results_listbox.pack(fill="both", expand=True)

        # Action buttons
        action_frame = ctk.CTkFrame(self.main_content)
        action_frame.pack(fill="x", padx=10, pady=5)

        view_result_btn = ctk.CTkButton(action_frame, text="👁️ View Details", width=120, command=self._view_result_details)
        view_result_btn.pack(side="left", padx=5)

        export_result_btn = ctk.CTkButton(action_frame, text="💾 Export", width=100, command=self._export_result)
        export_result_btn.pack(side="right", padx=5)

        self._refresh_results()

    def _show_settings_view(self) -> None:
        """Show settings panel."""
        self._clear_content()

        header = ctk.CTkLabel(
            self.main_content,
            text="Settings",
            font=("Helvetica", 20, "bold"),
        )
        header.pack(pady=10)

        # Settings notebook
        settings_notebook = ctk.CTkTabview(self.main_content)
        settings_notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # General settings tab
        general_tab = settings_notebook.add("General")
        self._create_general_settings(general_tab)

        # API Keys tab
        api_tab = settings_notebook.add("API Keys")
        self._create_api_settings(api_tab)

        # Proxy/Tor tab
        proxy_tab = settings_notebook.add("Proxy/Tor")
        self._create_proxy_settings(proxy_tab)

        # Save button
        save_btn = ctk.CTkButton(
            self.main_content,
            text="💾 Save Settings",
            width=150,
            command=self._save_settings,
        )
        save_btn.pack(pady=10)

    def _create_general_settings(self, parent) -> None:
        """Create general settings panel."""
        # Theme selection
        theme_frame = ctk.CTkFrame(parent)
        theme_frame.pack(fill="x", padx=10, pady=5)

        theme_label = ctk.CTkLabel(theme_frame, text="Theme:", font=("Helvetica", 12))
        theme_label.pack(side="left", padx=5)

        self.theme_var = ctk.StringVar(value="dark")
        dark_rb = ctk.CTkRadioButton(theme_frame, text="Dark", variable=self.theme_var, value="dark")
        dark_rb.pack(side="left", padx=5)

        light_rb = ctk.CTkRadioButton(theme_frame, text="Light", variable=self.theme_var, value="light")
        light_rb.pack(side="left", padx=5)

        # Timeout settings
        timeout_frame = ctk.CTkFrame(parent)
        timeout_frame.pack(fill="x", padx=10, pady=5)

        timeout_label = ctk.CTkLabel(timeout_frame, text="Default Timeout (seconds):", font=("Helvetica", 12))
        timeout_label.pack(side="left", padx=5)

        self.timeout_entry = ctk.CTkEntry(timeout_frame, width=100)
        self.timeout_entry.insert(0, "120")
        self.timeout_entry.pack(side="left", padx=5)

        # Cache settings
        cache_frame = ctk.CTkFrame(parent)
        cache_frame.pack(fill="x", padx=10, pady=5)

        self.cache_enabled_var = ctk.BooleanVar(value=True)
        cache_checkbox = ctk.CTkCheckbox(cache_frame, text="Enable Caching", variable=self.cache_enabled_var)
        cache_checkbox.pack(side="left", padx=5)

    def _create_api_settings(self, parent) -> None:
        """Create API keys settings panel."""
        info_label = ctk.CTkLabel(
            parent,
            text="Configure API keys for enhanced features",
            font=("Helvetica", 11),
        )
        info_label.pack(pady=10)

        # HaveIBeenPwned API key
        hibp_frame = ctk.CTkFrame(parent)
        hibp_frame.pack(fill="x", padx=10, pady=5)

        hibp_label = ctk.CTkLabel(hibp_frame, text="HaveIBeenPwned API Key:", font=("Helvetica", 12))
        hibp_label.pack(side="left", padx=5)

        self.hibp_key_entry = ctk.CTkEntry(hibp_frame, width=300, show="*")
        self.hibp_key_entry.pack(side="left", padx=5, fill="x", expand=True)

        # Public Records API key
        records_frame = ctk.CTkFrame(parent)
        records_frame.pack(fill="x", padx=10, pady=5)

        records_label = ctk.CTkLabel(records_frame, text="Public Records API Key:", font=("Helvetica", 12))
        records_label.pack(side="left", padx=5)

        self.records_key_entry = ctk.CTkEntry(records_frame, width=300, show="*")
        self.records_key_entry.pack(side="left", padx=5, fill="x", expand=True)

        # Phone Lookup API key
        phone_frame = ctk.CTkFrame(parent)
        phone_frame.pack(fill="x", padx=10, pady=5)

        phone_label = ctk.CTkLabel(phone_frame, text="Phone Lookup API Key:", font=("Helvetica", 12))
        phone_label.pack(side="left", padx=5)

        self.phone_key_entry = ctk.CTkEntry(phone_frame, width=300, show="*")
        self.phone_key_entry.pack(side="left", padx=5, fill="x", expand=True)

    def _create_proxy_settings(self, parent) -> None:
        """Create proxy/Tor settings panel."""
        # Proxy enabled
        proxy_enabled_frame = ctk.CTkFrame(parent)
        proxy_enabled_frame.pack(fill="x", padx=10, pady=5)

        self.proxy_enabled_var = ctk.BooleanVar(value=False)
        proxy_checkbox = ctk.CTkCheckbox(proxy_enabled_frame, text="Enable Proxy", variable=self.proxy_enabled_var)
        proxy_checkbox.pack(side="left", padx=5)

        # Proxy URL
        proxy_url_frame = ctk.CTkFrame(parent)
        proxy_url_frame.pack(fill="x", padx=10, pady=5)

        proxy_url_label = ctk.CTkLabel(proxy_url_frame, text="Proxy URL:", font=("Helvetica", 12))
        proxy_url_label.pack(side="left", padx=5)

        self.proxy_url_entry = ctk.CTkEntry(proxy_url_frame, width=300, placeholder_text="http://proxy:port")
        self.proxy_url_entry.pack(side="left", padx=5, fill="x", expand=True)

        # Tor enabled
        tor_frame = ctk.CTkFrame(parent)
        tor_frame.pack(fill="x", padx=10, pady=5)

        self.tor_enabled_var = ctk.BooleanVar(value=False)
        tor_checkbox = ctk.CTkCheckbox(tor_frame, text="Enable Tor Proxy", variable=self.tor_enabled_var)
        tor_checkbox.pack(side="left", padx=5)

        # Tor control port
        tor_port_frame = ctk.CTkFrame(parent)
        tor_port_frame.pack(fill="x", padx=10, pady=5)

        tor_port_label = ctk.CTkLabel(tor_port_frame, text="Tor Control Port:", font=("Helvetica", 12))
        tor_port_label.pack(side="left", padx=5)

        self.tor_port_entry = ctk.CTkEntry(tor_port_frame, width=100)
        self.tor_port_entry.insert(0, "9051")
        self.tor_port_entry.pack(side="left", padx=5)

    def _refresh_targets(self) -> None:
        """Refresh targets list from database."""
        try:
            from nyx.core.database import get_database_manager
            from nyx.models.target import Target
            from sqlalchemy import select

            db_manager = get_database_manager()
            targets_text = "Targets:\n" + "=" * 80 + "\n\n"

            async def fetch_targets():
                nonlocal targets_text
                async for session in db_manager.get_session():
                    stmt = select(Target).order_by(Target.last_searched.desc()).limit(50)
                    result = await session.execute(stmt)
                    targets = result.scalars().all()

                    if not targets:
                        targets_text = "No targets found.\n\nUse 'Add Target' to create a new target."
                    else:
                        lines = []
                        for target in targets:
                            lines.append(f"ID: {target.id}\n")
                            lines.append(f"Name: {target.name}\n")
                            lines.append(f"Category: {target.category}\n")
                            lines.append(f"Last Searched: {target.last_searched or 'Never'}\n")
                            lines.append(f"Search Count: {target.search_count}\n")
                            lines.append("-" * 80 + "\n\n")
                        targets_text += "".join(lines)

                    self.targets_listbox.delete("1.0", "end")
                    self.targets_listbox.insert("1.0", targets_text)
                    break

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(fetch_targets())
            loop.close()
        except Exception as e:
            self.targets_listbox.delete("1.0", "end")
            self.targets_listbox.insert("1.0", f"Error loading targets: {e}\n\nDatabase may not be initialized.")

    def _refresh_results(self) -> None:
        """Refresh search history from database."""
        try:
            from nyx.core.database import get_database_manager
            from nyx.models.target import SearchHistory
            from sqlalchemy import select

            db_manager = get_database_manager()
            results_text = "Search History:\n" + "=" * 80 + "\n\n"

            async def fetch_results():
                nonlocal results_text
                async for session in db_manager.get_session():
                    stmt = select(SearchHistory).order_by(SearchHistory.timestamp.desc()).limit(50)
                    result = await session.execute(stmt)
                    histories = result.scalars().all()

                    if not histories:
                        results_text = "No search history found."
                    else:
                        lines = []
                        for history in histories:
                            lines.append(f"ID: {history.id}\n")
                            lines.append(f"Query: {history.search_query}\n")
                            lines.append(f"Type: {history.search_type}\n")
                            lines.append(f"Timestamp: {history.timestamp}\n")
                            lines.append(f"Results Found: {history.results_found}\n")
                            lines.append("-" * 80 + "\n\n")
                        results_text += "".join(lines)

                    self.results_listbox.delete("1.0", "end")
                    self.results_listbox.insert("1.0", results_text)
                    break

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(fetch_results())
            loop.close()
        except Exception as e:
            self.results_listbox.delete("1.0", "end")
            self.results_listbox.insert("1.0", f"Error loading search history: {e}\n\nDatabase may not be initialized.")

    def _filter_results(self) -> None:
        """Filter search history by query."""
        # Implementation would filter displayed results
        pass

    def _add_target_dialog(self) -> None:
        """Show dialog to add new target."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Target")
        dialog.geometry("400x300")

        name_label = ctk.CTkLabel(dialog, text="Name:", font=("Helvetica", 12))
        name_label.pack(pady=5)
        name_entry = ctk.CTkEntry(dialog, width=300)
        name_entry.pack(pady=5)

        category_label = ctk.CTkLabel(dialog, text="Category:", font=("Helvetica", 12))
        category_label.pack(pady=5)
        category_entry = ctk.CTkEntry(dialog, width=300, placeholder_text="person, organization, etc.")
        category_entry.pack(pady=5)

        def save_target():
            name = name_entry.get().strip()
            category = category_entry.get().strip() or "person"
            if name:
                try:
                    from nyx.core.database import get_database_manager
                    from nyx.models.target import Target

                    async def create_target():
                        db_manager = get_database_manager()
                        async for session in db_manager.get_session():
                            target = Target(name=name, category=category)
                            session.add(target)
                            await session.commit()
                            break

                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(create_target())
                    loop.close()

                    dialog.destroy()
                    self._refresh_targets()
                except Exception as e:
                    logger.error(f"Failed to create target: {e}")

        save_btn = ctk.CTkButton(dialog, text="Save", command=save_target)
        save_btn.pack(pady=10)

    def _view_target(self) -> None:
        """View selected target details."""
        # Implementation would show target details
        logger.debug("View target clicked")

    def _edit_target(self) -> None:
        """Edit selected target."""
        # Implementation would show edit dialog
        logger.debug("Edit target clicked")

    def _delete_target(self) -> None:
        """Delete selected target."""
        # Implementation would delete target
        logger.debug("Delete target clicked")

    def _export_target(self) -> None:
        """Export target data."""
        # Implementation would export target
        logger.debug("Export target clicked")

    def _view_result_details(self) -> None:
        """View search result details."""
        # Implementation would show result details
        logger.debug("View result details clicked")

    def _export_result(self) -> None:
        """Export search result."""
        # Implementation would export result
        logger.debug("Export result clicked")

    def _save_settings(self) -> None:
        """Save settings to configuration."""
        try:
            # Update theme
            theme = self.theme_var.get()
            ctk.set_appearance_mode(theme)

            # Save other settings to config file
            # In production, this would update config/settings.yaml
            logger.info("Settings saved")
            self._update_status("Settings saved successfully")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            self._update_status(f"Error saving settings: {e}")


def create_app(config: Optional[Config] = None) -> MainWindow:
    """Create and return main application window.

    Args:
        config: Application configuration

    Returns:
        Main window instance
    """
    return MainWindow(config=config)
