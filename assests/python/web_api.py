#!/usr/bin/env python3
"""
Web API for Mantooth Blog Processor
Provides endpoints for the web interface
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from pathlib import Path
import sys

# Add better path handling
script_dir = Path(__file__).parent
project_root = None

# Try to find project root
search_paths = [
    script_dir.parent.parent,  # If in assests/python
    script_dir.parent,         # If in python
    Path.cwd(),               # Current directory
    Path.cwd().parent,        # Parent of current
]

for potential_root in search_paths:
    if (potential_root / "blogs.html").exists() and (potential_root / "assests").exists():
        project_root = potential_root
        break

if not project_root:
    print("❌ Could not find project root directory")
    print("Please run from the main @ManTooth@ directory")
    sys.exit(1)

print(f"✅ Project root found: {project_root}")

# Add project root to Python path
sys.path.insert(0, str(project_root / "assests" / "python"))

try:
    from mantooth_blog_processor import MantoothBlogProcessor
except ImportError as e:
    print(f"❌ Could not import blog processor: {e}")
    sys.exit(1)

app = Flask(__name__)
CORS(app)

# Initialize processor with correct project root
class CustomBlogProcessor(MantoothBlogProcessor):
    def __init__(self, project_root_path):
        self.project_root = Path(project_root_path)
        
        # Define paths
        self.raw_blogs_dir = self.project_root / "assests" / "Blogs" / "Raw Blogs"
        self.blogs_dir = self.project_root / "assests" / "Blogs"
        self.images_dir = self.project_root / "assests" / "Images"
        self.json_dir = self.project_root / "assests" / "JSON"
        
        self.blogs_html_path = self.project_root / "blogs.html"
        self.config_path = self.json_dir / "processing-config.json"
        self.blog_data_path = self.json_dir / "blog-data.json"
        
        # Create directories if needed
        self.blogs_dir.mkdir(parents=True, exist_ok=True)
        self.json_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self.load_configuration()
        
        print(f"📁 Raw Blogs directory: {self.raw_blogs_dir}")
        print(f"📁 Output directory: {self.blogs_dir}")

try:
    processor = CustomBlogProcessor(project_root)
    print("✅ Blog processor initialized successfully")
except Exception as e:
    print(f"❌ Error initializing processor: {e}")
    processor = None

@app.route('/')
def home():
    return jsonify({
        'service': 'Mantooth Blog Processor API',
        'version': '2.0.0',
        'endpoints': {
            'health': '/api/health',
            'list_pdfs': '/api/list-pdfs',
            'preview_pdf': '/api/preview-pdf',
            'process_pdf': '/api/process-pdf'
        },
        'status': 'running',
        'project_root': str(project_root)
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'OK',
        'service': 'Mantooth Blog Processor API',
        'version': '2.0.0',
        'processor_ready': processor is not None,
        'project_root': str(project_root),
        'raw_blogs_dir': str(processor.raw_blogs_dir) if processor else None
    })

@app.route('/api/list-pdfs', methods=['GET'])
def list_pdfs():
    """List available PDF files"""
    if not processor:
        return jsonify({'success': False, 'error': 'Processor not initialized'}), 500
    
    try:
        pdfs = processor.list_available_pdfs()
        pdf_list = []
        
        for pdf in pdfs:
            size_mb = pdf.stat().st_size / (1024 * 1024)
            pdf_list.append({
                'name': pdf.name,
                'path': str(pdf),
                'size_mb': round(size_mb, 2),
                'modified': pdf.stat().st_mtime
            })
        
        return jsonify({
            'success': True,
            'pdfs': pdf_list,
            'count': len(pdf_list),
            'raw_blogs_dir': str(processor.raw_blogs_dir)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ... rest of the endpoints remain the same ...

if __name__ == '__main__':
    print("🦷 Mantooth Blog Processor API")
    print("=" * 50)
    print(f"📁 Project root: {project_root}")
    
    if processor:
        print(f"📁 Raw Blogs directory: {processor.raw_blogs_dir}")
        print(f"📁 Output directory: {processor.blogs_dir}")
        print(f"📊 JSON directory: {processor.json_dir}")
    
    print("🌐 Starting server on http://localhost:5000")
    print("📋 Available endpoints:")
    print("   • http://localhost:5000/api/health")
    print("   • http://localhost:5000/api/list-pdfs")
    print("   • http://localhost:5000/api/preview-pdf")
    print("   • http://localhost:5000/api/process-pdf")
    print("✅ Ready to process blogs!")
    print("=" * 50)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")