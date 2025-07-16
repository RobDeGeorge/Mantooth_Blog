# Mantooth Blog

A complete blog management system for the Mantooth website, featuring automated PDF-to-blog processing with a modern GUI interface.

## Project Overview

Mantooth Blog is a personal blog platform with an innovative workflow that converts PDF documents into beautiful HTML blog posts. The system is designed for content creators who write their blog posts in PDF format and want an automated way to publish them to their website.

## Key Features

- PDF-to-Blog Processing - Converts PDF documents into structured HTML blog posts
- Modern GUI Interface - PySide6/QML application for easy blog management
- Smart Tagging System - Live editing of titles and tags with real-time updates
- Batch Processing - Process multiple PDFs at once or individually
- Automatic Image Detection - Matches PDF files with corresponding blog images
- Live Editing - Edit published blog titles and tags directly in the GUI
- Nuclear Reset - Quick cleanup tool to reset all blog data
- Maintenance Tools - Built-in cleanup utilities for duplicate removal

## Project Structure

```
blog-processor/              # Blog processing tools
├── images/                  # Blog post images
├── input/                   # PDF files to process
├── output/                  # Generated HTML blog posts
└── src/                     # Python source code
    ├── main.py              # Core blog processor
    ├── blog_manager.py      # Cleanup utilities
    └── gui/                 # PySide6/QML interface
        ├── blog_processor_gui.py
        ├── blog_processor_ui.qml
        └── BlogItemCard.qml

website/                     # Website files
├── assets/                  # Website assets
│   ├── css/                # Stylesheets
│   ├── js/                 # JavaScript files
│   ├── images/             # Website images
│   └── data/               # JSON data files
├── index.html              # Homepage
├── blogs.html              # Blog listing page
├── about.html              # About page
└── contact.html            # Contact page
```

## Getting Started

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd mantooth-blog
   ```

2. Set up virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   # GUI mode (default)
   python blog-processor/src/gui/blog_processor_gui.py
   
   # CLI mode
   python blog-processor/src/main.py
   
   # Cleanup tools
   python blog-processor/src/blog_manager.py
   ```

## How It Works

### Blog Creation Workflow

1. Write Content - Create your blog post as a PDF document
2. Add to Input - Place PDF in `blog-processor/input/`
3. Add Image - Add matching image to `blog-processor/images/`
4. Process - Use GUI or CLI to convert PDF to HTML
5. Tag & Edit - Add tags and edit title as needed
6. Publish - Generated blog appears on your website

### PDF Processing Features

- Smart Paragraph Detection - Handles various PDF formatting styles
- Title Extraction - Automatically extracts titles from PDF filenames
- Duplicate Prevention - Prevents processing the same PDF twice
- Image Matching - Automatically finds matching images for blog posts
- HTML Generation - Creates styled HTML with proper navigation

### GUI Features

- Live Preview - See blog content before publishing
- Real-time Editing - Edit titles and tags with instant updates
- Status Tracking - Visual indicators for processing status
- Batch Operations - Process multiple blogs simultaneously

## Website Features

- Responsive Design - Works on desktop and mobile
- Dynamic Content - Blog posts automatically added to listings
- Tag Filtering - Filter blogs by categories
- Recent Posts - Homepage shows latest blog entries
- Professional Layout - Clean, modern design

## Maintenance Tools

- Duplicate Cleanup - Remove duplicate blog entries
- Orphaned File Cleanup - Remove HTML files without JSON entries
- Data Rebuilding - Regenerate blog listings from JSON data
- Nuclear Reset - Complete system reset for fresh starts

## License

Private project - All rights reserved.# Test deployment
