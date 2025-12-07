"""Test script for verifying executable functionality."""

import sys
from pathlib import Path


def test_imports():
    """Test that all modules can be imported."""
    print("Testing module imports...")
    
    modules = [
        "nyx",
        "nyx.config",
        "nyx.core",
        "nyx.core.resource_paths",
        "nyx.core.version",
        "nyx.core.updater",
        "nyx.core.update_client",
        "nyx.core.update_service",
        "nyx.config.updater_config",
        "nyx.utils.update_utils",
    ]
    
    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            failed.append(module)
    
    return len(failed) == 0


def test_resource_paths():
    """Test resource path resolution."""
    print("\nTesting resource path resolution...")
    
    try:
        from nyx.core.resource_paths import (
            get_base_path,
            get_data_path,
            get_config_path,
            get_resource_path,
        )
        
        base = get_base_path()
        print(f"  ✓ Base path: {base}")
        
        data = get_data_path()
        print(f"  ✓ Data path: {data}")
        
        config = get_config_path()
        print(f"  ✓ Config path: {config}")
        
        resource = get_resource_path("data/platforms")
        print(f"  ✓ Resource path: {resource}")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_version():
    """Test version management."""
    print("\nTesting version management...")
    
    try:
        from nyx.core.version import get_current_version, parse_version, compare_versions
        
        current = get_current_version()
        print(f"  ✓ Current version: {current}")
        
        v1 = parse_version("1.2.3")
        v2 = parse_version("1.2.4")
        result = compare_versions("1.2.3", "1.2.4")
        print(f"  ✓ Version comparison: {result}")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_data_files():
    """Test data file loading."""
    print("\nTesting data file loading...")
    
    try:
        from nyx.core.resource_paths import get_resource_path
        
        # Check for platform files
        platforms_dir = get_resource_path("data/platforms")
        if platforms_dir.exists():
            json_files = list(platforms_dir.glob("*.json"))
            print(f"  ✓ Found {len(json_files)} platform JSON files")
        else:
            print(f"  ⚠ Platform directory not found: {platforms_dir}")
        
        # Check for config
        config_file = get_resource_path("config/settings.yaml")
        if config_file.exists():
            print(f"  ✓ Config file found: {config_file}")
        else:
            print(f"  ⚠ Config file not found: {config_file}")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Nyx Executable Test Suite")
    print("="*60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Resource Paths", test_resource_paths),
        ("Version Management", test_version),
        ("Data Files", test_data_files),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for name, passed in results.items():
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n⚠ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

