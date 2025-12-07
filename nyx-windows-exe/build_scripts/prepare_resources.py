"""Prepare resources for bundling into executable."""

import json
import shutil
import sys
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        # Python < 3.7 or reconfigure failed, use workaround
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")


def prepare_resources():
    """Copy and prepare all resources for bundling."""
    # Get paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    resources_dir = script_dir.parent / "resources"
    
    print("Preparing resources for executable build...")
    
    # Create resources directory structure
    resources_dir.mkdir(parents=True, exist_ok=True)
    (resources_dir / "data" / "platforms").mkdir(parents=True, exist_ok=True)
    (resources_dir / "config").mkdir(parents=True, exist_ok=True)
    
    # Copy platform JSON files
    source_platforms = project_root / "data" / "platforms"
    dest_platforms = resources_dir / "data" / "platforms"
    
    if source_platforms.exists():
        print(f"Copying platform files from {source_platforms}...")
        json_files = [
            "maigret_extended_platforms.json",
            "maigret_international_platforms.json",
            "maigret_niche_platforms.json",
        ]
        
        copied_count = 0
        for json_file in json_files:
            source_file = source_platforms / json_file
            if source_file.exists():
                dest_file = dest_platforms / json_file
                shutil.copy2(source_file, dest_file)
                print(f"  [OK] Copied {json_file}")
                copied_count += 1
            else:
                print(f"  [WARN] Missing {json_file} (skipping)")
        
        # Check for custom_platforms.json (optional)
        custom_file = source_platforms / "custom_platforms.json"
        if custom_file.exists():
            shutil.copy2(custom_file, dest_platforms / "custom_platforms.json")
            print(f"  [OK] Copied custom_platforms.json")
            copied_count += 1
        
        print(f"Copied {copied_count} platform file(s)")
    else:
        print(f"[WARN] Platform directory not found: {source_platforms}")
    
    # Copy default config
    source_config = project_root / "config" / "settings.yaml"
    dest_config = resources_dir / "config" / "settings.yaml"
    
    if source_config.exists():
        print(f"Copying config from {source_config}...")
        shutil.copy2(source_config, dest_config)
        print(f"  [OK] Copied settings.yaml")
    else:
        print(f"[WARN] Config file not found: {source_config}")
        # Create a minimal default config
        default_config = """debug: false
data_dir: ./data
config_dir: ./config

database:
  url: sqlite:///./nyx.db
  pool_size: 20
  max_overflow: 40
  echo: false

http:
  timeout: 10
  retries: 3
  user_agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Nyx/0.1.0
  max_concurrent_requests: 100

cache:
  enabled: true
  ttl: 3600
  max_size: 1000
  backend: memory

gui:
  theme: dark
  window_width: 1400
  window_height: 900
  font_size: 10

security:
  enable_encryption: true
  require_master_password: true
  password_hash_iterations: 100000
  session_timeout: 3600

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file_path: logs/nyx.log
  max_file_size: 10485760
  backup_count: 5

proxy:
  enabled: false
  http_proxy: null
  https_proxy: null
  socks_proxy: null

tor:
  enabled: false
  socks_host: 127.0.0.1
  socks_port: 9050
  control_host: 127.0.0.1
  control_port: 9051
  use_new_identity: false

updater:
  enabled: true
  source: github
  github_repo: null
  custom_url: null
  check_on_startup: true
  check_frequency: daily
  auto_download: false
  auto_install: false
  channel: stable
  skip_versions: []
"""
        dest_config.write_text(default_config, encoding="utf-8")
        print(f"  [OK] Created default settings.yaml")
    
    # Validate resources
    print("\nValidating resources...")
    validation_errors = []
    
    # Check platform files
    platform_files = list(dest_platforms.glob("*.json"))
    if not platform_files:
        validation_errors.append("No platform JSON files found")
    else:
        for pf in platform_files:
            try:
                with open(pf, "r", encoding="utf-8") as f:
                    json.load(f)
                print(f"  [OK] Valid JSON: {pf.name}")
            except json.JSONDecodeError as e:
                validation_errors.append(f"Invalid JSON in {pf.name}: {e}")
    
    # Check config file
    if not dest_config.exists():
        validation_errors.append("Config file missing")
    else:
        print(f"  [OK] Config file exists")
    
    if validation_errors:
        print("\n[WARN] Validation errors:")
        for error in validation_errors:
            print(f"  - {error}")
        return False
    
    print("\n[OK] All resources prepared successfully!")
    return True


if __name__ == "__main__":
    success = prepare_resources()
    exit(0 if success else 1)

