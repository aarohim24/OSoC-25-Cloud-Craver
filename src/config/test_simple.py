#!/usr/bin/env python3
"""
Simple configuration test script to debug issues.
"""

def test_basic_imports():
    """Test basic Python imports first."""
    try:
        import sys
        import os
        from pathlib import Path
        print("✅ Basic imports successful")
        return True
    except Exception as e:
        print(f"❌ Basic imports failed: {e}")
        return False

def test_dynaconf_import():
    """Test dynaconf import."""
    try:
        from dynaconf import Dynaconf
        print("✅ Dynaconf import successful")
        return True
    except Exception as e:
        print(f"❌ Dynaconf import failed: {e}")
        print("   You may need to install dynaconf: pip install dynaconf")
        return False

def test_config_files():
    """Test that configuration files exist."""
    try:
        from pathlib import Path
        config_dir = Path(__file__).parent
        
        files_to_check = [
            "settings.toml",
            "config.yaml", 
            "base_config.toml"
        ]
        
        for file_name in files_to_check:
            file_path = config_dir / file_name
            if file_path.exists():
                print(f"✅ {file_name} exists")
            else:
                print(f"❌ {file_name} missing")
        
        return True
    except Exception as e:
        print(f"❌ File check failed: {e}")
        return False

def test_config_loading():
    """Test configuration loading."""
    try:
        # Try to load configuration manually first
        import toml
        from pathlib import Path
        
        config_dir = Path(__file__).parent
        settings_file = config_dir / "settings.toml"
        
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                config_data = toml.load(f)
            print("✅ TOML file loaded successfully")
            print(f"   App name: {config_data.get('app', {}).get('name', 'Not found')}")
        else:
            print("❌ settings.toml not found")
        
        return True
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False

def test_dynaconf_configuration():
    """Test Dynaconf configuration loading."""
    try:
        from dynaconf import Dynaconf
        from pathlib import Path
        
        config_dir = Path(__file__).parent
        
        settings = Dynaconf(
            settings_files=[
                str(config_dir / "settings.toml"),
            ],
            envvar_prefix="CLOUDCRAVER",
            environments=False,  # Disable environments for simple test
        )
        
        print("✅ Dynaconf configuration created")
        print(f"   App name: {getattr(settings, 'app', {}).get('name', 'Not found')}")
        print(f"   Settings keys: {list(settings.keys())}")
        
        return True
    except Exception as e:
        print(f"❌ Dynaconf configuration failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🔍 Cloud Craver Configuration Debug")
    print("=" * 50)
    
    tests = [
        ("Basic imports", test_basic_imports),
        ("Dynaconf import", test_dynaconf_import), 
        ("Configuration files", test_config_files),
        ("Config file loading", test_config_loading),
        ("Dynaconf configuration", test_dynaconf_configuration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n🎯 {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Configuration system should be working.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main() 