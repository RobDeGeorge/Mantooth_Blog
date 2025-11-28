#!/usr/bin/env python3
"""
Simple launcher for the Mantooth Blog Processor GUI
"""

import sys
from pathlib import Path

# Add the GUI source directory to the path
gui_dir = Path(__file__).parent / "src" / "gui"
sys.path.insert(0, str(gui_dir))

# Import and run the GUI
from blog_processor_gui import main

if __name__ == "__main__":
    sys.exit(main())