"""Build all executable variants."""

import subprocess
import sys
from pathlib import Path


def build_all():
    """Build all executable variants."""
    script_dir = Path(__file__).parent
    specs_dir = script_dir.parent / "specs"
    build_script = script_dir / "build.py"
    
    specs = [
        "nyx-gui-onefile.spec",
        "nyx-gui-folder.spec",
        "nyx-cli-onefile.spec",
        "nyx-cli-folder.spec",
        "nyx-launcher.spec",
    ]
    
    print("="*60)
    print("Building all Nyx executable variants")
    print("="*60)
    
    results = {}
    
    for spec in specs:
        spec_path = specs_dir / spec
        if not spec_path.exists():
            print(f"⚠ Spec file not found: {spec}")
            results[spec] = False
            continue
        
        print(f"\n{'='*60}")
        print(f"Building: {spec}")
        print(f"{'='*60}")
        
        result = subprocess.run(
            [
                sys.executable,
                str(build_script),
                "--spec",
                str(spec_path),
                "--manifest",
            ],
            cwd=script_dir.parent.parent,
        )
        
        results[spec] = result.returncode == 0
    
    # Summary
    print("\n" + "="*60)
    print("Build Summary")
    print("="*60)
    
    for spec, success in results.items():
        status = "✓" if success else "❌"
        print(f"{status} {spec}")
    
    all_success = all(results.values())
    
    if all_success:
        print("\n✓ All builds completed successfully!")
    else:
        print("\n⚠ Some builds failed. Check output above for details.")
    
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(build_all())

