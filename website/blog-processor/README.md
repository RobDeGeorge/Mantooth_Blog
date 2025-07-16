# Mantooth Blog Processor (Pure GUI)

A streamlined PySide6/QML GUI application for processing PDF files into blog posts for the Mantooth website.

## What It Does

- Scans for PDF files in `input/` folder
- Extracts text and detects paragraphs automatically
- Lets you add tags and select images via clean GUI
- Generates HTML blog posts and updates the website
- No CLI prompts or command-line dependencies

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r ../requirements.txt
   ```

2. **Run the GUI:**
   ```bash
   python3 run_gui.py
   ```

3. **Usage:**
   - Put PDF files in `input/` folder
   - Put blog images in `images/` folder  
   - Run the GUI, add tags, select images
   - Click "Process" to generate blog posts

## File Structure

```
blog-processor/
├── run_gui.py          # Launch the GUI
├── README.md           # This file
├── input/              # Put PDF files here
├── images/             # Put blog images here
├── output/             # Generated HTML files
└── src/gui/            # Pure GUI source code
    ├── blog_processor_gui.py  # Streamlined GUI logic (no CLI)
    ├── blog_processor_ui.qml  # UI interface
    └── BlogItemCard.qml       # Blog item component
```

## Features

- ✅ PDF text extraction (pdfplumber)
- ✅ Smart paragraph detection
- ✅ Tag management via GUI
- ✅ Image selection via GUI
- ✅ Duplicate cleanup
- ✅ Live preview
- ✅ Batch processing
- ✅ Pure GUI - no CLI components

**All CLI-style interactive prompts, print statements, and command-line oriented code have been completely removed.**