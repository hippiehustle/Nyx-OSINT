"""Main build script for creating Nyx executables."""

import argparse
import hashlib
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

# Fix Windows console encoding for Unicode characters
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        # Python < 3.7 or reconfigure failed, use workaround
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")


def load_build_config() -> dict:
    """Load build configuration."""
    script_dir = Path(__file__).parent
    config_path = script_dir.parent / "build_config.yaml"
    
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def get_version() -> str:
    """Get current version from package."""
    try:
        from nyx import __version__
        return __version__
    except ImportError:
        # Fallback to config
        config = load_build_config()
        return config.get("version", "0.1.0")


def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        SHA256 checksum as hex string
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def build_executable(spec_path: Path, dist_dir: Path, config: dict) -> bool:
    """Build executable from spec file.
    
    Args:
        spec_path: Path to PyInstaller spec file
        dist_dir: Output directory
        config: Build configuration
        
    Returns:
        True if build successful
    """
    print(f"\n{'='*60}")
    print(f"Building: {spec_path.name}")
    print(f"{'='*60}")
    
    if not spec_path.exists():
        print(f"[ERROR] Spec file not found: {spec_path}")
        return False
    
    try:
        # Run PyInstaller
        cmd = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            str(spec_path),
        ]
        
        # Add distpath if specified
        if dist_dir:
            cmd.extend(["--distpath", str(dist_dir)])
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("[OK] Build completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Build failed:")
        print(e.stdout)
        print(e.stderr)
        return False
    except Exception as e:
        print(f"[ERROR] Error during build: {e}")
        return False


def generate_update_manifest(executable_path: Path, config: dict) -> dict:
    """Generate update manifest for built executable.
    
    Args:
        executable_path: Path to built executable
        config: Build configuration
        
    Returns:
        Update manifest dictionary
    """
    version = get_version()
    file_size = executable_path.stat().st_size if executable_path.exists() else 0
    checksum = calculate_checksum(executable_path) if executable_path.exists() else ""
    
    manifest = {
        "version": version,
        "release_date": datetime.now().isoformat(),
        "channel": config.get("update", {}).get("channel", "stable"),
        "installer": {
            "filename": executable_path.name,
            "size": file_size,
            "checksum": f"sha256:{checksum}",
        },
        "changelog": "See release notes",
        "release_notes": "",
        "min_version": "0.1.0",
        "critical": False,
        "prerelease": False,
    }
    
    return manifest


def main():
    """Main build function."""
    parser = argparse.ArgumentParser(description="Build Nyx Windows executables")
    parser.add_argument(
        "--spec",
        type=str,
        help="Path to PyInstaller spec file",
    )
    parser.add_argument(
        "--dist",
        type=str,
        help="Output directory (default: dist/)",
    )
    parser.add_argument(
        "--manifest",
        action="store_true",
        help="Generate update manifest",
    )
    
    args = parser.parse_args()
    
    # Load config
    config = load_build_config()
    
    # Get paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    specs_dir = script_dir.parent / "specs"
    dist_dir = Path(args.dist) if args.dist else script_dir.parent / "dist"
    
    # Prepare resources first
    print("Preparing resources...")
    prepare_script = script_dir / "prepare_resources.py"
    if prepare_script.exists():
        result = subprocess.run(
            [sys.executable, str(prepare_script)],
            cwd=project_root,
        )
        if result.returncode != 0:
            print("[ERROR] Resource preparation failed")
            return 1
    else:
        print("[WARN] Resource preparation script not found")
    
    # Build executable
    if args.spec:
        spec_path = Path(args.spec)
        if not spec_path.is_absolute():
            # If path already starts with "specs", use it as-is relative to project
            if spec_path.parts[0] == "specs":
                spec_path = script_dir.parent / spec_path
            else:
                spec_path = specs_dir / spec_path
    else:
        print("[ERROR] No spec file specified. Use --spec to specify a spec file.")
        return 1
    
    if not build_executable(spec_path, dist_dir, config):
        return 1
    
    # Generate manifest if requested
    if args.manifest:
        # Find the built executable
        exe_name = spec_path.stem.replace("_", "-")
        exe_base_name = f"{exe_name.split('-')[0]}-{exe_name.split('-')[1]}.exe"
        if "onefile" in exe_name:
            # Onefile builds: executable is directly in dist_dir
            exe_path = dist_dir / exe_base_name
        else:
            # Onedir/folder builds: executable is in a subdirectory
            exe_path = dist_dir / exe_name / exe_base_name
        
        if exe_path.exists():
            manifest = generate_update_manifest(exe_path, config)
            manifest_path = dist_dir / f"{exe_name}_manifest.json"
            with open(manifest_path, "w", encoding="utf-8") as f:
                import json
                json.dump(manifest, f, indent=2)
            print(f"[OK] Update manifest generated: {manifest_path}")
    
    print("\n[OK] Build process completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

