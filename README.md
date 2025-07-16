# 🦷 Mantooth - Personal Blog Platform

[![Live Website](https://img.shields.io/badge/Live%20Site-mantooth.me-blue?style=for-the-badge)](https://mantooth.me)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)](https://python.org)
[![PySide6](https://img.shields.io/badge/PySide6-GUI-green?style=flat-square)](https://doc.qt.io/qtforpython/)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow?style=flat-square&logo=javascript)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)

**Visit the live website: [mantooth.me](https://mantooth.me)**

A sophisticated personal blog platform with a unique PDF-to-blog workflow, featuring a modern PySide6/QML GUI application and a responsive web interface. Mantooth transforms the traditional blogging experience by allowing content creation in PDF format and automating the conversion to beautiful HTML blog posts.

---

## 🌟 What Makes Mantooth Special

Mantooth is a **complete end-to-end blogging solution** that bridges the gap between content creation and web publishing. Unlike traditional blog platforms, Mantooth allows you to:

- **Write in PDF format** - Create rich, formatted content in your favorite PDF editor
- **Automate publishing** - Convert PDFs to web-ready HTML with a single click
- **Manage visually** - Use a modern GUI application for all blog management tasks
- **Deploy instantly** - Generated content automatically integrates with your website

The platform consists of two main components:
1. **Desktop Application** - PySide6/QML GUI for processing and managing blog content
2. **Web Platform** - Responsive website with dynamic content loading and satellite imagery

---

## 🎯 Core Features

### 📄 PDF-to-Blog Processing
- **Smart Text Extraction** - Uses `pdfplumber` for accurate PDF content parsing
- **Intelligent Paragraph Detection** - Automatically formats text into readable web content
- **Title Extraction** - Derives blog titles from PDF filenames
- **Duplicate Prevention** - Prevents reprocessing of existing content
- **Batch Processing** - Handle multiple PDFs simultaneously

### 🎨 Modern GUI Interface
- **PySide6/QML Application** - Native desktop experience with modern UI
- **Live Preview** - See your blog content before publishing
- **Tag Management** - Add and edit tags with real-time updates
- **Image Selection** - Visual interface for associating images with posts
- **Status Tracking** - Clear visual indicators for processing status
- **Maintenance Tools** - Built-in cleanup and data management utilities

### 🌐 Dynamic Website
- **Responsive Design** - Optimized for desktop and mobile viewing
- **Satellite Imagery** - Random NASA Earth imagery on the homepage
- **Tag Filtering** - Interactive filtering system for blog discovery
- **Recent Posts** - Automatically updated homepage content
- **Lazy Loading** - Optimized image loading for better performance
- **Modern JavaScript** - ES6+ features for enhanced user experience

---

## 🏗️ Project Architecture

```
@ManTooth@/
├── 🌐 website/                    # Live website (mantooth.me)
│   ├── 📄 index.html             # Homepage with satellite imagery
│   ├── 📄 blogs.html             # Blog listing with filtering
│   ├── 📄 about.html             # About page
│   ├── 📄 contact.html           # Contact information
│   ├── 🎨 assets/
│   │   ├── css/style.css         # Responsive styles
│   │   ├── js/                   # Interactive features
│   │   │   ├── blog-generator.js # Dynamic blog loading
│   │   │   ├── tag-filter.js     # Tag filtering system
│   │   │   ├── recent-posts.js   # Homepage content
│   │   │   ├── image-optimizer.js # Lazy loading
│   │   │   └── clickable-cards.js # Interactive elements
│   │   ├── data/blog-data.json   # Dynamic blog metadata
│   │   └── images/               # Satellite and blog images
│   └── 📁 blog-processor/        # Processing tools
│       ├── 🔧 run_gui.py         # GUI launcher
│       ├── 📁 input/             # PDF files for processing
│       ├── 📁 images/            # Blog post images
│       ├── 📁 output/            # Generated HTML files
│       └── 📁 src/gui/           # PySide6/QML application
├── 🐍 requirements.txt           # Python dependencies
├── 🚀 run.sh                     # Automated runner script
├── 📋 CNAME                      # Domain configuration
└── 📖 README.md                  # This file
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** with pip
- **Virtual environment** support
- **Linux/macOS/Windows** with GUI support

### Installation & Setup

1. **Clone and navigate:**
   ```bash
   git clone <repository-url>
   cd @ManTooth@
   ```

2. **Set up Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the application:**
   ```bash
   # Use the automated runner (recommended)
   ./run.sh                  # GUI version
   ./run.sh --cli           # Terminal version
   ./run.sh --cleanup       # Maintenance tools
   
   # Or run directly
   python website/blog-processor/run_gui.py
   ```

---

## 📝 Content Creation Workflow

### 1. Create Content
- Write your blog post in any PDF editor
- Save with a descriptive filename (becomes the title)
- Place in `website/blog-processor/input/`

### 2. Add Visual Assets
- Add a corresponding image to `website/blog-processor/images/`
- Use matching filenames for automatic association

### 3. Process with GUI
- Launch the GUI application
- Select your PDF from the list
- Add tags and customize metadata
- Click "Process" to generate HTML

### 4. Publish
- Generated blog appears automatically on your website
- Content is added to the blog listing with tags
- Recent posts section updates automatically

---

## 🛠️ Technical Implementation

### Desktop Application Stack
- **PySide6** - Qt6 bindings for Python, providing native GUI
- **QML** - Declarative UI framework for modern interfaces
- **pdfplumber** - Advanced PDF text extraction and parsing

### Web Platform Stack
- **Vanilla JavaScript (ES6+)** - Modern web features without frameworks
- **Responsive CSS3** - Mobile-first design with flexbox/grid
- **JSON-based CMS** - Dynamic content management without databases
- **Lazy Loading** - Performance optimization for images
- **NASA API Integration** - Dynamic satellite imagery

### Key Features Implementation

#### PDF Processing Engine
```python
# Smart paragraph detection and content extraction
# Handles various PDF formatting styles
# Preserves text structure and readability
```

#### Dynamic Content Loading
```javascript
// Real-time blog loading with tag filtering
// Lazy image loading for performance
// Interactive card-based interface
```

#### Responsive Design
```css
/* Mobile-first approach */
/* Flexbox and Grid layouts */
/* Optimized for all screen sizes */
```

---

## 🌐 Live Website Features

**Visit: [mantooth.me](https://mantooth.me)**

### Homepage
- **Dynamic Satellite Imagery** - Random NASA Earth photos on each visit
- **Recent Posts** - Latest blog entries with visual previews
- **Responsive Navigation** - Consistent across all devices

### Blog Section
- **Tag-based Filtering** - Interactive category system
- **Search Functionality** - Find content quickly
- **Clickable Cards** - Intuitive blog discovery
- **Mobile Optimization** - Perfect reading experience on any device

### Content Types
Current blog topics include:
- **Music & Concerts** - Live music experiences and reviews
- **Local Restaurants** - Food and dining recommendations
- **Travel & Events** - Adventure stories and local attractions
- **Lifestyle & Pets** - Personal insights and experiences

---

## 🔧 Maintenance & Management

### Built-in Tools
- **Duplicate Cleanup** - Remove redundant blog entries
- **Orphaned File Management** - Clean up unused HTML files
- **Data Rebuilding** - Regenerate blog listings from JSON
- **Nuclear Reset** - Complete system reset for fresh starts

### Development Scripts
```bash
# Run different modes
./run.sh --cli           # Command-line interface
./run.sh --cleanup       # Maintenance tools
./run.sh                 # GUI application (default)
```

---

## 🎯 Use Cases & Applications

### Personal Blogging
- **Content Creators** who prefer rich-text PDF editing
- **Writers** wanting automated web publishing
- **Photographers** needing visual blog management

### Professional Applications
- **Portfolio Sites** with dynamic content management
- **Business Blogs** requiring consistent formatting
- **Educational Content** with structured presentation

---

## 🤝 Contributing & Development

This is a **personal project** showcasing:
- **Full-stack development** skills
- **Desktop application** development with PySide6/QML
- **Modern web development** with vanilla JavaScript
- **Creative problem-solving** with unique PDF-to-web workflow
- **User experience design** with intuitive interfaces

---

## 📄 License

**Private project** - All rights reserved.

---

## 🔗 Links & Resources

- **Live Website:** [mantooth.me](https://mantooth.me)
- **GitHub Pages:** Automated deployment
- **Domain:** Custom domain with CNAME configuration

---

*Built with ❤️ using Python, PySide6, JavaScript, and a passion for innovative content management solutions.*
