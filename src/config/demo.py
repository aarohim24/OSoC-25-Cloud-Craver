#!/usr/bin/env python3
"""
Cloud Craver Configuration Demo

This script demonstrates the various features of the Dynaconf configuration system
including configuration loading, validation, user preferences, and CLI integration.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from dynaconf import Dynaconf
        print("✅ Dynaconf import successful")
    except ImportError as e:
        print(f"❌ Dynaconf import failed: {e}")
        print("   Please install dynaconf: pip install dynaconf")
        return False
    
    try:
        # Add the src directory to the path for imports
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from config import config
        print("✅ Config module import successful")
    except ImportError as e:
        print(f"❌ Config module import failed: {e}")
        print("   Make sure you're running from the correct directory")
        return False
    
    return True

def demo_basic_configuration():
    """Demonstrate basic configuration access."""
    print("\n" + "=" * 60)
    print("BASIC CONFIGURATION ACCESS")
    print("=" * 60)
    
    from config import config, get_cloud_config, get_user_preferences, get_app_config
    
    # Access configuration sections
    print("📋 Application Configuration:")
    app_config = get_app_config()
    print(f"  • Name: {app_config.name}")
    print(f"  • Version: {app_config.version}")
    print(f"  • Debug: {app_config.debug}")
    print(f"  • Log Level: {app_config.log_level}")
    
    print("\n☁️  Cloud Configuration:")
    cloud_config = get_cloud_config()
    print(f"  • Default Provider: {cloud_config.default_provider}")
    print(f"  • Available Providers: {cloud_config.providers}")
    print(f"  • AWS Region: {cloud_config.aws.region}")
    print(f"  • Azure Location: {cloud_config.azure.location}")
    
    print("\n👤 User Preferences:")
    user_prefs = get_user_preferences()
    print(f"  • Default Provider: {user_prefs.default_provider}")
    print(f"  • Default Region: {user_prefs.default_region}")
    print(f"  • Auto Save: {user_prefs.auto_save}")
    print(f"  • Theme: {user_prefs.theme}")

def demo_configuration_sources():
    """Demonstrate configuration file discovery and precedence."""
    print("\n\n" + "=" * 60)
    print("CONFIGURATION SOURCES & PRECEDENCE")
    print("=" * 60)
    
    from config import get_config_sources
    from config.utils import discover_config_files
    
    # Show configuration sources
    print("📁 Configuration Sources (in precedence order):")
    sources = get_config_sources()
    for i, source in enumerate(sources, 1):
        print(f"  {i}. {source}")
    
    # Discover configuration files
    print("\n🔍 Discovered Configuration Files:")
    discovered = discover_config_files()
    for file_type, files in discovered.items():
        if files:
            print(f"  • {file_type.upper()} files:")
            for file_path in files[:3]:  # Limit to first 3 files
                print(f"    - {file_path}")

def demo_simple_config_access():
    """Demonstrate simple configuration access without complex dependencies."""
    print("\n\n" + "=" * 60)
    print("SIMPLE CONFIGURATION ACCESS")
    print("=" * 60)
    
    try:
        from config import config
        print("✅ Configuration loaded successfully!")
        
        # Try to access basic configuration
        if hasattr(config, 'app'):
            print(f"📱 App Name: {config.app.name}")
            print(f"📱 App Version: {config.app.version}")
        
        if hasattr(config, 'cloud'):
            print(f"☁️  Default Provider: {config.cloud.default_provider}")
            print(f"☁️  Available Providers: {config.cloud.providers}")
        
        print("\n🔧 Configuration keys available:")
        keys = list(config.keys())
        for key in keys[:10]:  # Show first 10 keys
            print(f"  • {key}")
        
        if len(keys) > 10:
            print(f"  ... and {len(keys) - 10} more")
        
    except Exception as e:
        print(f"❌ Error accessing configuration: {e}")

def main():
    """Main demo function."""
    print("🚀 Cloud Craver Configuration System Demo")
    print("📋 This demo showcases the configuration features")
    print("=" * 60)
    
    # Test imports first
    if not test_imports():
        print("\n❌ Import test failed. Cannot continue with demo.")
        print("\n🔧 To fix this:")
        print("   1. Make sure you have a virtual environment activated")
        print("   2. Install dependencies: pip install -r ../../requirements.txt")
        print("   3. Run from src/config/ directory")
        print("\n💡 You can also try the simple test: python3 test_simple.py")
        return 1
    
    try:
        # Start with simple demos that don't require complex dependencies
        demo_simple_config_access()
        demo_basic_configuration()
        demo_configuration_sources()
        
        print("\n\n" + "=" * 60)
        print("✅ BASIC DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\n📚 For more advanced features:")
        print("  • User preferences management")
        print("  • CLI integration") 
        print("  • Configuration validation")
        print("  • Environment variable handling")
        print("\n📖 See README.md for complete documentation")
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("\n🔧 Try running test_simple.py first to diagnose the issue:")
        print("   python3 test_simple.py")
        return 1
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        print("\n🔧 Try running test_simple.py first to diagnose the issue:")
        print("   python3 test_simple.py")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 