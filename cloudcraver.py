#!/usr/bin/env python3
"""
Cloud Craver Entry Point

This script provides the main entry point for the Cloud Craver application.
It handles the package imports and module path setup correctly.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path so imports work correctly
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Now we can import and run the main application
if __name__ == "__main__":
    try:
        from main import main
        main()
    except ImportError as e:
        print(f"Error importing main module: {e}")
        print("Make sure you're running this from the project root directory.")
        sys.exit(1)
    except Exception as e:
        print(f"Error running application: {e}")
        sys.exit(1) 