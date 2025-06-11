#!/usr/bin/env python3
"""
Simple launcher for the Mantooth Blog Processor
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from mantooth_blog_processor import MantoothBlogProcessor
    
    def main():
        print("🦷 Mantooth Blog Generator")
        print("Starting interactive blog processor...")
        print()
        
        processor = MantoothBlogProcessor()
        processor.run_interactive()

    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure pdfplumber is installed: pip install pdfplumber")
except Exception as e:
    print(f"❌ Error: {e}")