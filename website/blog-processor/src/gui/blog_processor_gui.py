#!/usr/bin/env python3
"""
Mantooth Blog Processor GUI
PySide6/QML interface for blog processing
"""

import sys
import os
import json
import re
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from PySide6.QtCore import QObject, Signal, Slot, Property, QAbstractListModel, QModelIndex, Qt, QUrl, QThread
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import qmlRegisterType, QmlElement
from PySide6.QtQuickControls2 import QQuickStyle

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed. Run: pip install pdfplumber")
    sys.exit(1)

QML_IMPORT_NAME = "BlogProcessor"
QML_IMPORT_MAJOR_VERSION = 1

class BlogProcessor:
    """Pure GUI blog processor - no CLI components"""
    def __init__(self):
        self.project_root = self.find_project_root()
        if not self.project_root:
            raise Exception("Could not find project root")
        
        # Define paths
        self.raw_blogs_dir = self.project_root / "website" / "blog-processor" / "input"
        self.blogs_dir = self.project_root / "website" / "blog-processor" / "output"
        self.blog_images_dir = self.project_root / "website" / "blog-processor" / "images"
        self.json_dir = self.project_root / "website" / "assets" / "data"
        self.blogs_html_path = self.project_root / "website" / "blogs.html"
        self.blog_data_path = self.json_dir / "blog-data.json"
        
        # Create directories
        self.blogs_dir.mkdir(parents=True, exist_ok=True)
        self.blog_images_dir.mkdir(parents=True, exist_ok=True)
        self.json_dir.mkdir(parents=True, exist_ok=True)

    def find_project_root(self) -> Optional[Path]:
        """Find project root by looking for key files"""
        script_path = Path(__file__).parent
        search_paths = [
            script_path.parent.parent.parent,  # From gui/src/ to project root
            Path.cwd(),
        ]
        
        for root in search_paths:
            if (root / "website" / "blogs.html").exists():
                return root
        return None

    def list_available_pdfs(self) -> List[Path]:
        """List all available PDF files"""
        if not self.raw_blogs_dir.exists():
            return []
        return list(self.raw_blogs_dir.glob("*.pdf"))

    def extract_text_from_pdf(self, pdf_path: Path) -> Optional[Dict]:
        """Extract text from PDF"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text
                
                if not full_text.strip():
                    return None
                
                paragraphs = self.detect_paragraphs(full_text)
                return {
                    'paragraphs': paragraphs,
                    'text': '\n\n'.join(paragraphs),
                    'total_pages': len(pdf.pages),
                    'total_paragraphs': len(paragraphs)
                }
        except Exception:
            return None

    def detect_paragraphs(self, text: str) -> List[str]:
        """Robust paragraph detection"""
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    
        paragraphs: List[str] = []
        current: List[str] = []
    
        for line in lines:
            raw = line.rstrip()
            if not raw.strip():
                if current:
                    paragraphs.append(self.clean_paragraph_text(" ".join(current)))
                    current = []
                continue
    
            indent = len(raw) - len(raw.lstrip())
            new_para = False
    
            if indent >= 2 and current:
                new_para = True
            elif (current and
                  current[-1][-1] in ".?!" and
                  raw.lstrip()[:1].isupper()):
                new_para = True
    
            if new_para:
                paragraphs.append(self.clean_paragraph_text(" ".join(current)))
                current = [raw.strip()]
            else:
                current.append(raw.strip())
    
        if current:
            paragraphs.append(self.clean_paragraph_text(" ".join(current)))

        return paragraphs

    def clean_paragraph_text(self, text: str) -> str:
        """Clean up paragraph text"""
        # Remove hyphenation at line ends
        text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Fix quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text

    def parse_preview_content(self, preview_content: str) -> List[str]:
        """Parse edited preview content back to paragraphs"""
        if not preview_content.strip():
            return []
        
        # Split by double newlines to get paragraph blocks
        blocks = preview_content.split('\n\n')
        paragraphs = []
        
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            
            # Remove paragraph numbers like [1], [2], etc.
            # Handle cases like "[1] text" or just "text"
            import re
            cleaned = re.sub(r'^\[\d+\]\s*', '', block)
            if cleaned.strip():
                paragraphs.append(cleaned.strip())
        
        return paragraphs

    def format_content_to_html(self, paragraphs: List[str], title: str) -> str:
        """Convert paragraphs to HTML content"""
        if not paragraphs:
            return ""

        html_elements = [f"                    <h3>{self.escape_html(title)}</h3>"]
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if para.endswith(':') and len(para) < 30:
                html_elements.append(f"                    <h3>{self.escape_html(para.rstrip(':'))}</h3>")
            else:
                html_elements.append(f"                    <p>{self.escape_html(para)}</p>")

        return "\n\n".join(html_elements)

    def escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#39;')
        return text

    def generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug"""
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug).strip('-')
        return f"{slug}-blog"

    def extract_title_from_filename(self, filename: str) -> str:
        """Extract title from PDF filename"""
        title = filename.replace('.pdf', '').replace('_', ' ')
        title = re.sub(r'[^\w\s]', ' ', title)
        title = ' '.join(word.capitalize() for word in title.split())
        return title

    def generate_excerpt(self, paragraphs: List[str], max_length: int = 200) -> str:
        """Generate excerpt from paragraphs"""
        for para in paragraphs:
            if not (para.endswith(':') and len(para) < 50):
                if len(para) <= max_length:
                    return para
                else:
                    excerpt = para[:max_length]
                    last_space = excerpt.rfind(' ')
                    if last_space > max_length * 0.8:
                        excerpt = excerpt[:last_space]
                    return excerpt + "..."
        return "No excerpt available."

    def list_available_images(self) -> List[str]:
        """List all available image files in the blog images directory"""
        if not self.blog_images_dir.exists():
            return []
        
        image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.webp']
        images = []
        
        for ext in image_extensions:
            images.extend(self.blog_images_dir.glob(ext))
            images.extend(self.blog_images_dir.glob(ext.upper()))
        
        return [img.name for img in sorted(images)]

    def create_blog_html(self, blog_data: Dict) -> str:
        """Generate blog HTML file"""
        template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Mantooth</title>
    <link rel="stylesheet" href="../../assets/css/style.css">
</head>
<body>
    <header>
        <div class="container">
            <h1 class="logo">Mantooth</h1>
            <nav>
                <ul>
                    <li><a href="../../index.html">Home</a></li>
                    <li><a href="../../blogs.html" class="active">Blogs</a></li>
                    <li><a href="../../about.html">About</a></li>
                    <li><a href="../../contact.html">Contact</a></li>
                </ul>
            </nav>
        </div>
    </header>

    <main>
        <div class="container">
            <article class="blog-post">
                <h2 class="blog-title">{title}</h2>
                <p class="post-meta">Posted on {formatted_date}</p>
                
{featured_image_html}
                
                <div class="blog-content">
{content}
                </div>
                
                <div class="blog-tags">
{tags_html}
                </div>
            </article>
        </div>
    </main>

    <footer>
        <div class="container">
            <p>&copy; 2025 Mantooth. All Rights Reserved.</p>
            <div class="social-links">
                <a href="#">Facebook</a>
                <a href="#">Instagram</a>
            </div>
        </div>
    </footer>

    <script src="../../assets/js/image-optimizer.js"></script>
    <script src="../../assets/js/clickable-cards.js"></script>
</body>
</html>'''
        
        tags_html = '\n'.join([f'                    <span class="tag">{tag.title()}</span>' for tag in blog_data['tags']])
        
        # Generate image HTML only if there's an image with lazy loading
        featured_image = blog_data.get('featured_image', '')
        if featured_image and featured_image.strip():
            featured_image_html = f'                <img data-src="../images/{featured_image}" alt="{blog_data["title"]}" class="blog-featured-image lazy-loading">'
        else:
            featured_image_html = '                <!-- No featured image -->'
        
        return template.format(
            title=blog_data['title'],
            formatted_date=blog_data['formatted_date'],
            featured_image_html=featured_image_html,
            content=blog_data['content'],
            tags_html=tags_html
        )

    def update_blogs_html(self, blog_data: Dict) -> bool:
        """Update blogs.html with new entry"""
        if not self.blogs_html_path.exists():
            return False
        
        try:
            with open(self.blogs_html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            grid_start = content.find('<section class="blogs-grid">')
            grid_end = content.find('</section>', grid_start)
            
            if grid_start == -1 or grid_end == -1:
                return False
            
            item_html = f'''                <!-- Blog Post - {blog_data['title']} -->
                <article class="blog-item clickable-card" data-tags="{','.join(blog_data['tags'])}" data-url="blog-processor/output/{blog_data['slug']}.html">
                    <img data-src="blog-processor/images/{blog_data['featured_image']}?v={int(time.time())}" alt="{blog_data['title']}" class="lazy-loading">
                    <div class="blog-content">
                        <h3>{blog_data['title']}</h3>
                        <p class="post-meta">Posted on {blog_data['formatted_date']}</p>
                        <p>{blog_data['excerpt']}</p>
                        <div class="blog-footer">
                            <div class="blog-tags">
                                {' '.join([f'<span class="tag">{tag.title()}</span>' for tag in blog_data['tags']])}
                            </div>
                        </div>
                    </div>
                </article>'''
            
            existing_section = content[grid_start:grid_end + 10]
            insertion_point = existing_section.find('>', existing_section.find('<section class="blogs-grid">')) + 1
            
            updated_section = (existing_section[:insertion_point] + 
                                '\n' + item_html + '\n                \n' + 
                                existing_section[insertion_point:])
            
            updated_html = content[:grid_start] + updated_section + content[grid_end + 10:]
            
            with open(self.blogs_html_path, 'w', encoding='utf-8') as f:
                f.write(updated_html)
            
            return True
        except Exception:
            return False

    def update_blog_data_json(self, new_blogs: List[Dict]):
        """Update blog-data.json"""
        try:
            if self.blog_data_path.exists():
                with open(self.blog_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {"posts": []}
            
            for blog in reversed(new_blogs):
                post_data = {
                    "id": blog['slug'].replace('-blog', '-2025'),
                    "title": blog['title'],
                    "slug": blog['slug'],
                    "publishDate": blog['publish_date'],
                    "excerpt": blog['excerpt'],
                    "featuredImage": blog['featured_image'],
                    "tags": blog['tags'],
                    "readTime": self.calculate_read_time(blog['content']),
                    "fileName": f"{blog['slug']}.html",
                    "createdAt": datetime.now().isoformat(),
                    "source": "GUI Processing",
                    "sourceFile": blog.get('source_file', ''),
                    "paragraphCount": blog.get('paragraph_count', 0),
                    "editedContent": blog.get('edited_content', '')  # Store the edited preview content
                }
                
                # Check if post already exists and update it instead of duplicating
                existing_index = None
                for i, existing_post in enumerate(data["posts"]):
                    if existing_post.get("slug") == blog['slug']:
                        existing_index = i
                        break
                
                if existing_index is not None:
                    # Update existing post
                    post_data["lastUpdated"] = datetime.now().isoformat()
                    data["posts"][existing_index] = post_data
                else:
                    # Insert new post at the beginning
                    data["posts"].insert(0, post_data)
            
            data["lastUpdated"] = datetime.now().isoformat()
            data["totalPosts"] = len(data["posts"])
            
            with open(self.blog_data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def calculate_read_time(self, content: str) -> int:
        """Calculate estimated reading time"""
        text = re.sub(r'<[^>]+>', '', content)
        words = len(text.split())
        return max(1, round(words / 200))

class BlogManager:
    def __init__(self):
        self.processor = BlogProcessor()
        self.blogs_dir = self.processor.blogs_dir
        self.blog_data_path = self.processor.blog_data_path
        self.blogs_html_path = self.processor.blogs_html_path
    
    def get_existing_blogs(self) -> Dict:
        """Get existing blog data"""
        try:
            if self.blog_data_path.exists():
                with open(self.blog_data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"posts": [], "totalPosts": 0}
        except Exception:
            return {"posts": [], "totalPosts": 0}
    
    def find_duplicates(self) -> Dict[str, List[Dict]]:
        """Find duplicate blog posts by slug"""
        blog_data = self.get_existing_blogs()
        duplicates = defaultdict(list)
        
        for post in blog_data.get("posts", []):
            slug = post.get("slug", "")
            if slug:
                duplicates[slug].append(post)
        
        return {slug: posts for slug, posts in duplicates.items() if len(posts) > 1}
    
    def clean_duplicates(self, keep_latest=True) -> int:
        """Remove duplicate entries, keeping only the latest or first"""
        blog_data = self.get_existing_blogs()
        duplicates = self.find_duplicates()
        
        if not duplicates:
            return 0
        
        # Remove duplicates
        cleaned_posts = []
        seen_slugs = set()
        removed_count = 0
        
        # Sort posts by creation date
        all_posts = blog_data.get("posts", [])
        if keep_latest:
            all_posts.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
        else:
            all_posts.sort(key=lambda x: x.get("createdAt", ""))
        
        for post in all_posts:
            slug = post.get("slug", "")
            if slug not in seen_slugs:
                cleaned_posts.append(post)
                seen_slugs.add(slug)
            else:
                removed_count += 1
        
        # Update blog data
        blog_data["posts"] = cleaned_posts
        blog_data["totalPosts"] = len(cleaned_posts)
        blog_data["lastUpdated"] = datetime.now().isoformat()
        
        # Save cleaned data
        with open(self.blog_data_path, 'w', encoding='utf-8') as f:
            json.dump(blog_data, f, indent=2)
        
        return removed_count
    
    def rebuild_blogs_html(self):
        """Rebuild blogs.html from JSON data"""
        blog_data = self.get_existing_blogs()
        posts = blog_data.get("posts", [])
        
        # Continue even if no posts to generate clean empty blogs.html
        
        # Template parts
        template_start = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mantooth - Blogs</title>
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
    <header>
        <div class="container">
            <h1 class="logo">Mantooth</h1>
            <nav>
                <ul>
                    <li><a href="index.html">Home</a></li>
                    <li><a href="blogs.html" class="active">Blogs</a></li>
                    <li><a href="about.html">About</a></li>
                    <li><a href="contact.html">Contact</a></li>
                </ul>
            </nav>
        </div>
    </header>

    <main>
        <div class="container">
            <section class="blogs-header">
                <h2>All Blog Posts</h2>
                <p>Explore my collection of thoughts, stories, and insights</p>
            </section>

            <section class="blogs-grid">'''

        template_end = '''
                <!-- New blog posts will be added here automatically by the Python processor -->
                
            </section>
        </div>
    </main>

    <footer>
        <div class="container">
            <p>&copy; 2025 Mantooth. All Rights Reserved.</p>
            <div class="social-links">
                <a href="#">Facebook</a>
                <a href="#">Instagram</a>
            </div>
        </div>
    </footer>

    <script src="assets/js/image-optimizer.js"></script>
    <script src="assets/js/tag-filter.js"></script>
    <script src="assets/js/clickable-cards.js"></script>
    <script>
        // Initialize image lazy loading
        document.addEventListener('DOMContentLoaded', function() {
            const imageOptimizer = new ImageOptimizer();
            document.querySelectorAll('img.lazy-loading').forEach(img => {
                imageOptimizer.addLazyImage(img);
            });
        });
    </script>
</body>
</html>'''
        
        # Generate blog items HTML
        blog_items = []
        for post in posts:
            tags_html = ' '.join([f'<span class="tag">{tag.title()}</span>' for tag in post.get('tags', [])])
            
            item_html = f'''                <!-- Blog Post - {post.get('title', 'Unknown')} -->
                <article class="blog-item clickable-card" data-tags="{','.join(post.get('tags', []))}" data-url="blog-processor/output/{post.get('fileName', '')}">
                    <img data-src="blog-processor/images/{post.get('featuredImage', '')}?v={int(time.time())}" alt="{post.get('title', '')}" class="lazy-loading">
                    <div class="blog-content">
                        <h3>{post.get('title', '')}</h3>
                        <p class="post-meta">Posted on {datetime.fromisoformat(post.get('publishDate', '2025-01-01')).strftime('%B %d, %Y')}</p>
                        <p>{post.get('excerpt', '')}</p>
                        <div class="blog-footer">
                            <div class="blog-tags">
                                {tags_html}
                            </div>
                        </div>
                    </div>
                </article>'''
            blog_items.append(item_html)
        
        # Combine everything
        full_html = template_start + '\n'.join(blog_items) + template_end
        
        # Write to file
        with open(self.blogs_html_path, 'w', encoding='utf-8') as f:
            f.write(full_html)

@QmlElement
class BlogItem(QObject):
    """Individual blog item for the UI"""
    
    titleChanged = Signal()
    slugChanged = Signal()
    excerptChanged = Signal()
    tagsChanged = Signal()
    imagePathChanged = Signal()
    statusChanged = Signal()
    previewContentChanged = Signal()
    originalContentChanged = Signal()
    pdfPathChanged = Signal()
    
    def __init__(self, pdf_path: str = "", parent=None):
        super().__init__(parent)
        self._title = ""
        self._slug = ""
        self._excerpt = ""
        self._tags = []
        self._image_path = ""
        self._status = "pending"  # pending, processing, completed, error
        self._pdf_path = pdf_path
        self._preview_content = ""
        self._original_content = ""
        
    @Property(str, notify=titleChanged)
    def title(self):
        return self._title
    
    @title.setter
    def title(self, value):
        if self._title != value:
            self._title = value
            self.titleChanged.emit()
    
    @Property(str, notify=slugChanged)
    def slug(self):
        return self._slug
    
    @slug.setter
    def slug(self, value):
        if self._slug != value:
            self._slug = value
            self.slugChanged.emit()
    
    @Property(str, notify=excerptChanged)
    def excerpt(self):
        return self._excerpt
    
    @excerpt.setter
    def excerpt(self, value):
        if self._excerpt != value:
            self._excerpt = value
            self.excerptChanged.emit()
    
    @Property(list, notify=tagsChanged)
    def tags(self):
        return self._tags
    
    @tags.setter
    def tags(self, value):
        if self._tags != value:
            self._tags = value
            self.tagsChanged.emit()
    
    @Property(str, notify=imagePathChanged)
    def imagePath(self):
        return self._image_path
    
    @imagePath.setter
    def imagePath(self, value):
        if self._image_path != value:
            self._image_path = value
            self.imagePathChanged.emit()
    
    @Property(str, notify=statusChanged)
    def status(self):
        return self._status
    
    @status.setter
    def status(self, value):
        if self._status != value:
            self._status = value
            self.statusChanged.emit()
    
    @Property(str)
    def pdfPath(self):
        return self._pdf_path
    
    @Property(str, notify=previewContentChanged)
    def previewContent(self):
        return self._preview_content
    
    @previewContent.setter
    def previewContent(self, value):
        if self._preview_content != value:
            self._preview_content = value
            self.previewContentChanged.emit()
    
    @Property(str, notify=originalContentChanged)
    def originalContent(self):
        return self._original_content
    
    @originalContent.setter
    def originalContent(self, value):
        if self._original_content != value:
            self._original_content = value
            self.originalContentChanged.emit()

@QmlElement
class BlogListModel(QAbstractListModel):
    """Model for blog items in the UI"""
    
    TitleRole = Qt.UserRole + 1
    SlugRole = Qt.UserRole + 2
    ExcerptRole = Qt.UserRole + 3
    TagsRole = Qt.UserRole + 4
    ImagePathRole = Qt.UserRole + 5
    StatusRole = Qt.UserRole + 6
    PdfPathRole = Qt.UserRole + 7
    PreviewContentRole = Qt.UserRole + 8
    OriginalContentRole = Qt.UserRole + 9
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: List[BlogItem] = []
    
    def roleNames(self):
        return {
            self.TitleRole: b"title",
            self.SlugRole: b"slug", 
            self.ExcerptRole: b"excerpt",
            self.TagsRole: b"tags",
            self.ImagePathRole: b"imagePath",
            self.StatusRole: b"status",
            self.PdfPathRole: b"pdfPath",
            self.PreviewContentRole: b"previewContent",
            self.OriginalContentRole: b"originalContent"
        }
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._items)
    
    def data(self, index, role):
        if not index.isValid() or index.row() >= len(self._items):
            return None
        
        item = self._items[index.row()]
        
        if role == self.TitleRole:
            return item.title
        elif role == self.SlugRole:
            return item.slug
        elif role == self.ExcerptRole:
            return item.excerpt
        elif role == self.TagsRole:
            return item.tags
        elif role == self.ImagePathRole:
            return item.imagePath
        elif role == self.StatusRole:
            return item.status
        elif role == self.PdfPathRole:
            return item.pdfPath
        elif role == self.PreviewContentRole:
            return item.previewContent
        elif role == self.OriginalContentRole:
            return item.originalContent
        
        return None
    
    def addItem(self, item: BlogItem):
        self.beginInsertRows(QModelIndex(), len(self._items), len(self._items))
        self._items.append(item)
        self.endInsertRows()
    
    def clear(self):
        self.beginResetModel()
        self._items.clear()
        self.endResetModel()
    
    @Slot(int, result=QObject)
    def getItem(self, index: int) -> Optional[BlogItem]:
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

class ProcessingThread(QThread):
    """Background thread for PDF processing"""
    
    progressUpdate = Signal(int, str)  # index, status
    itemProcessed = Signal(int, dict)  # index, blog_data
    finished = Signal()
    
    def __init__(self, processor: BlogProcessor, items: List[BlogItem]):
        super().__init__()
        self.processor = processor
        self.items = items
    
    def run(self):
        for i, item in enumerate(self.items):
            try:
                self.progressUpdate.emit(i, "processing")
                
                # Extract text from PDF
                pdf_path = Path(item.pdfPath)
                extraction_result = self.processor.extract_text_from_pdf(pdf_path)
                
                if not extraction_result:
                    self.progressUpdate.emit(i, "error")
                    continue
                
                paragraphs = extraction_result['paragraphs']
                
                # Use edited preview content if available, otherwise use extracted paragraphs
                if item.previewContent.strip():
                    # Parse the edited preview content
                    paragraphs = self.processor.parse_preview_content(item.previewContent)
                
                # Generate blog data
                title = self.processor.extract_title_from_filename(pdf_path.name)
                slug = self.processor.generate_slug(title)
                content_html = self.processor.format_content_to_html(paragraphs, title)
                excerpt = self.processor.generate_excerpt(paragraphs)
                # Use the image selected in the UI (if any)
                featured_image = item.imagePath if item.imagePath else ""
                
                blog_data = {
                    'title': title,
                    'slug': slug,
                    'content': content_html,
                    'excerpt': excerpt,
                    'featured_image': featured_image,
                    'paragraphs': paragraphs,
                    'paragraph_count': len(paragraphs),
                    'pdf_path': str(pdf_path),
                    'edited_content': item.previewContent  # Store the edited content from UI
                }
                
                self.itemProcessed.emit(i, blog_data)
                self.progressUpdate.emit(i, "completed")
                
            except Exception as e:
                pass
                self.progressUpdate.emit(i, "error")
        
        self.finished.emit()

@QmlElement
class BlogProcessorBackend(QObject):
    """Main backend controller for the blog processor UI"""
    
    statusChanged = Signal(str)
    progressChanged = Signal(int, int)  # current, total
    itemsChanged = Signal()
    processingFinished = Signal()
    preserveCurrentPage = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._status = "ready"
        self._processor = BlogProcessor()
        self._blog_manager = BlogManager()
        self._blog_model = BlogListModel()
        self._processing_thread = None
    
    @Property(str, notify=statusChanged)
    def status(self):
        return self._status
    
    @status.setter
    def status(self, value):
        if self._status != value:
            self._status = value
            self.statusChanged.emit(value)
    
    @Property(QObject, constant=True)
    def blogModel(self):
        return self._blog_model
    
    @Slot(result=str)
    def getProjectRoot(self):
        """Get the absolute path to the project root"""
        return str(self._processor.project_root)
    
    @Slot()
    def scanForPdfs(self):
        """Scan for PDF files and populate the model"""
        self.status = "scanning and auto-loading content..."
        self._blog_model.clear()
        
        try:
            pdfs = self._processor.list_available_pdfs()
            published_data = self._blog_manager.get_existing_blogs()
            published_posts = {post.get("slug", ""): post for post in published_data.get("posts", [])}
            
            for pdf_path in pdfs:
                item = BlogItem(str(pdf_path))
                
                # Extract basic info
                title = self._processor.extract_title_from_filename(pdf_path.name)
                slug = self._processor.generate_slug(title)
                # No default image - can be selected before or after processing
                image_path = ""
                
                # Auto-load content from PDF
                try:
                    extraction_result = self._processor.extract_text_from_pdf(pdf_path)
                    if extraction_result:
                        paragraphs = extraction_result['paragraphs']
                        # Generate preview content (clean text without numbers)
                        preview_lines = []
                        for para in paragraphs:
                            para = para.strip()
                            if not para:
                                continue
                            preview_lines.append(para)
                        
                        preview_content = '\n\n'.join(preview_lines)
                        excerpt = self._processor.generate_excerpt(paragraphs)
                    else:
                        preview_content = ""
                        excerpt = "Failed to extract content from PDF"
                except Exception as e:
                    preview_content = ""
                    excerpt = f"Error loading PDF: {str(e)}"
                
                # Check if already published and get existing data
                if slug in published_posts:
                    published_post = published_posts[slug]
                    # Only use existing tags if they match the current PDF source file
                    source_file_matches = published_post.get("sourceFile", "") == pdf_path.name
                    item.title = published_post.get("title", title)
                    item.tags = published_post.get("tags", []) if source_file_matches else []
                    item.status = "published"
                    item.excerpt = published_post.get("excerpt", excerpt)
                    # Load existing featured image
                    item.imagePath = published_post.get("featuredImage", "")
                    # Use saved edited content if available, otherwise use auto-loaded
                    saved_content = published_post.get("editedContent", "")
                    item.previewContent = saved_content if saved_content else preview_content
                else:
                    item.title = title
                    item.tags = []
                    item.status = "pending"
                    item.excerpt = excerpt
                    item.imagePath = image_path
                    item.previewContent = preview_content
                
                item.slug = slug
                
                self._blog_model.addItem(item)
            
            published_count = len([item for item in range(self._blog_model.rowCount()) 
                                 if self._blog_model.getItem(item).status == "published"])
            
            self.status = f"loaded {len(pdfs)} PDFs with content ({published_count} already published)"
            self.itemsChanged.emit()
            
        except Exception as e:
            self.status = f"error: {e}"
    
    @Slot(int, str)
    def updateItemTags(self, index: int, tags_string: str):
        """Update tags for a specific item"""
        item = self._blog_model.getItem(index)
        if item:
            tags = [tag.strip().lower() for tag in tags_string.split(',') if tag.strip()]
            item.tags = tags
            # Notify the model that this item's data has changed
            model_index = self._blog_model.index(index, 0)
            self._blog_model.dataChanged.emit(model_index, model_index, [self._blog_model.TagsRole])
    
    @Slot(int, str)
    def updateItemTitle(self, index: int, new_title: str):
        """Update title for a specific item"""
        item = self._blog_model.getItem(index)
        if item:
            item.title = new_title.strip()
            # Notify the model that this item's data has changed
            model_index = self._blog_model.index(index, 0)
            self._blog_model.dataChanged.emit(model_index, model_index, [self._blog_model.TitleRole])
    
    @Slot(int)
    def updatePublishedBlog(self, index: int):
        """Update an already published blog with new title/tags"""
        item = self._blog_model.getItem(index)
        if not item or not item.tags:
            self.status = "Please add tags before updating"
            return
        
        try:
            self.status = f"updating {item.title}..."
            
            # Get the existing blog data
            blog_data = self._blog_manager.get_existing_blogs()
            posts = blog_data.get("posts", [])
            
            # Use the item's current slug to find the post
            current_slug = item.slug
            
            # Generate new excerpt from updated content
            if item.previewContent.strip():
                paragraphs = self._processor.parse_preview_content(item.previewContent)
            else:
                # Fallback to PDF extraction
                pdf_path = Path(item.pdfPath)
                extraction_result = self._processor.extract_text_from_pdf(pdf_path)
                paragraphs = extraction_result['paragraphs'] if extraction_result else []
            
            new_excerpt = self._processor.generate_excerpt(paragraphs) if paragraphs else ""
            
            # Update the post in JSON data
            updated = False
            for post in posts:
                if post.get("slug") == current_slug:
                    post["title"] = item.title
                    post["tags"] = item.tags
                    post["featuredImage"] = item.imagePath if item.imagePath else ""
                    post["editedContent"] = item.previewContent  # Save the edited content
                    post["excerpt"] = new_excerpt  # Update the excerpt
                    post["lastUpdated"] = datetime.now().isoformat()
                    updated = True
                    break
            
            if updated:
                # Save updated JSON
                blog_data["lastUpdated"] = datetime.now().isoformat()
                with open(self._blog_manager.blog_data_path, 'w', encoding='utf-8') as f:
                    json.dump(blog_data, f, indent=2)
                
                # Rebuild blogs.html with updated data
                self._blog_manager.rebuild_blogs_html()
                
                # Update HTML file if it exists
                html_file = self._processor.blogs_dir / f"{current_slug}.html"
                if html_file.exists():
                    # Re-extract PDF content and regenerate HTML with new title/tags
                    pdf_path = Path(item.pdfPath)
                    extraction_result = self._processor.extract_text_from_pdf(pdf_path)
                    if extraction_result:
                        paragraphs = extraction_result['paragraphs']
                        
                        # Use edited preview content if available
                        if item.previewContent.strip():
                            paragraphs = self._processor.parse_preview_content(item.previewContent)
                        
                        content_html = self._processor.format_content_to_html(paragraphs, item.title)
                        excerpt = self._processor.generate_excerpt(paragraphs)
                        # Use the image selected in the UI
                        featured_image = item.imagePath if item.imagePath else ""
                        
                        blog_data_for_html = {
                            'title': item.title,
                            'slug': current_slug,
                            'content': content_html,
                            'excerpt': excerpt,
                            'tags': item.tags,
                            'featured_image': featured_image,
                            'publish_date': datetime.now().strftime("%Y-%m-%d"),
                            'formatted_date': datetime.now().strftime("%B %d, %Y"),
                            'source_file': pdf_path.name
                        }
                        
                        # Regenerate HTML
                        blog_html = self._processor.create_blog_html(blog_data_for_html)
                        with open(html_file, 'w', encoding='utf-8') as f:
                            f.write(blog_html)
                
                self.status = f"✅ updated {item.title}"
                # Refresh to show changes
                self.scanForPdfs()
            else:
                self.status = "Blog not found in published posts"
                
        except Exception as e:
            self.status = f"update error: {e}"
            pass
    
    @Slot(int)
    def deletePublishedBlog(self, index: int):
        """Delete a specific published blog"""
        item = self._blog_model.getItem(index)
        if not item or item.status != "published":
            self.status = "Can only delete published blogs"
            return
        
        try:
            self.status = f"unpublishing {item.title}..."
            
            # Remove from blog-data.json
            blog_data = self._blog_manager.get_existing_blogs()
            posts = blog_data.get("posts", [])
            
            # Find and remove the post
            updated_posts = [post for post in posts if post.get("slug") != item.slug]
            
            if len(updated_posts) < len(posts):
                # Update JSON data
                blog_data["posts"] = updated_posts
                blog_data["totalPosts"] = len(updated_posts)
                blog_data["lastUpdated"] = datetime.now().isoformat()
                
                with open(self._blog_manager.blog_data_path, 'w', encoding='utf-8') as f:
                    json.dump(blog_data, f, indent=2)
                
                # Remove HTML file
                html_file = self._processor.blogs_dir / f"{item.slug}.html"
                if html_file.exists():
                    html_file.unlink()
                
                # Rebuild blogs.html
                self._blog_manager.rebuild_blogs_html()
                
                self.status = f"✅ unpublished {item.title}"
                # Signal to preserve current page before refresh
                self.preserveCurrentPage.emit()
                # Refresh to show changes
                self.scanForPdfs()
            else:
                self.status = "Blog not found in published posts"
                
        except Exception as e:
            self.status = f"delete error: {e}"
    
    @Slot()
    def nukeAllBlogs(self):
        """Nuclear option - clear all blogs and reset to blank state"""
        try:
            self.status = "nuking all blogs..."
            
            # Clear blog-data.json
            empty_data = {
                "posts": [],
                "lastUpdated": datetime.now().isoformat(),
                "totalPosts": 0
            }
            with open(self._blog_manager.blog_data_path, 'w', encoding='utf-8') as f:
                json.dump(empty_data, f, indent=2)
            
            # Reset blogs.html to empty state
            empty_blogs_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mantooth - Blogs</title>
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
    <header>
        <div class="container">
            <h1 class="logo">Mantooth</h1>
            <nav>
                <ul>
                    <li><a href="index.html">Home</a></li>
                    <li><a href="blogs.html" class="active">Blogs</a></li>
                    <li><a href="about.html">About</a></li>
                    <li><a href="contact.html">Contact</a></li>
                </ul>
            </nav>
        </div>
    </header>

    <main>
        <div class="container">
            <section class="blogs-header">
                <h2>All Blog Posts</h2>
                <p>Explore my collection of thoughts, stories, and insights</p>
            </section>

            <section class="blogs-grid">
                <!-- New blog posts will be added here automatically by the Python processor -->
                
            </section>
        </div>
    </main>

    <footer>
        <div class="container">
            <p>&copy; 2025 Mantooth. All Rights Reserved.</p>
            <div class="social-links">
                <a href="#">Twitter</a>
                <a href="#">Facebook</a>
                <a href="#">Instagram</a>
            </div>
        </div>
    </footer>

    <script src="assets/js/tag-filter.js"></script>
    <script src="assets/js/clickable-cards.js"></script>
</body>
</html>'''
            
            with open(self._blog_manager.blogs_html_path, 'w', encoding='utf-8') as f:
                f.write(empty_blogs_html)
            
            # Remove all generated HTML files
            if self._processor.blogs_dir.exists():
                for html_file in self._processor.blogs_dir.glob("*.html"):
                    try:
                        html_file.unlink()
                    except Exception as e:
                        pass
            
            self.status = "💥 all blogs nuked - fresh start ready"
            # Refresh to show clean state
            self.scanForPdfs()
            
        except Exception as e:
            self.status = f"nuke error: {e}"
    
    @Slot(int)
    def processSingleItem(self, index: int):
        """Process a single item by index"""
        if self._processing_thread and self._processing_thread.isRunning():
            self.status = "Already processing - please wait"
            return
        
        item = self._blog_model.getItem(index)
        if not item:
            self.status = "Invalid item"
            return
            
        if item.status == "published":
            self.status = "Blog already published"
            return
            
        if not item.tags:
            self.status = "Please add tags before processing"
            return
        
        self.status = f"processing {item.title}..."
        self._processing_thread = ProcessingThread(self._processor, [item])
        self._processing_thread.progressUpdate.connect(self._onProgressUpdate)
        self._processing_thread.itemProcessed.connect(self._onItemProcessed)
        self._processing_thread.finished.connect(self._onProcessingFinished)
        self._processing_thread.start()
    
    @Slot()
    def processAllItems(self):
        """Process all items in the model"""
        if self._processing_thread and self._processing_thread.isRunning():
            return
        
        items = [self._blog_model.getItem(i) for i in range(self._blog_model.rowCount())]
        # Only process unpublished items with tags
        items = [item for item in items if item and item.tags and item.status != "published"]
        
        if not items:
            self.status = "No unpublished items with tags to process"
            return
        
        self.status = "processing all items..."
        self._processing_thread = ProcessingThread(self._processor, items)
        self._processing_thread.progressUpdate.connect(self._onProgressUpdate)
        self._processing_thread.itemProcessed.connect(self._onItemProcessed)
        self._processing_thread.finished.connect(self._onProcessingFinished)
        self._processing_thread.start()
    
    @Slot()
    def cleanupDuplicates(self):
        """Clean up duplicate blog entries"""
        try:
            self.status = "cleaning duplicates..."
            removed_count = self._blog_manager.clean_duplicates(keep_latest=True)
            self._blog_manager.rebuild_blogs_html()
            self.status = f"cleaned {removed_count} duplicates"
            # Refresh the list
            self.scanForPdfs()
        except Exception as e:
            self.status = f"cleanup error: {e}"
    
    @Slot(int, str)
    def _onProgressUpdate(self, index: int, status: str):
        """Handle progress updates from processing thread"""
        item = self._blog_model.getItem(index)
        if item:
            item.status = status
    
    @Slot(int, dict)
    def _onItemProcessed(self, index: int, blog_data: dict):
        """Handle completed item processing"""
        item = self._blog_model.getItem(index)
        if not item:
            return
        
        try:
            # Generate HTML file
            blog_data['tags'] = item.tags
            blog_data['publish_date'] = datetime.now().strftime("%Y-%m-%d")
            blog_data['formatted_date'] = datetime.now().strftime("%B %d, %Y")
            blog_data['source_file'] = Path(item.pdfPath).name
            # featured_image was already set correctly in the processing thread
            
            blog_html = self._processor.create_blog_html(blog_data)
            blog_file_path = self._processor.blogs_dir / f"{blog_data['slug']}.html"
            
            with open(blog_file_path, 'w', encoding='utf-8') as f:
                f.write(blog_html)
            
            # Update JSON data first, then rebuild HTML to ensure scripts are included
            self._processor.update_blog_data_json([blog_data])
            self._blog_manager.rebuild_blogs_html()
            
            item.excerpt = blog_data['excerpt']
            
        except Exception as e:
            pass
            item.status = "error"
    
    @Slot(result=list)
    def getAvailableImages(self):
        """Get list of available images from blog-processor/images folder"""
        try:
            available_images = self._processor.list_available_images()
            return available_images
        except Exception as e:
            pass
            return []
    
    @Slot(result=str)
    def getProjectRootPath(self):
        """Get the project root path for QML"""
        root_path = str(self._processor.project_root)
        return root_path
    
    @Slot(str, result=str)
    def getImagePath(self, imageName):
        """Get the full file path for an image"""
        if not imageName:
            return ""
        
        # Extract just the filename if it has a path
        if "/" in imageName:
            imageName = imageName.split("/")[-1]
        
        full_path = self._processor.blog_images_dir / imageName
        file_url = f"file://{full_path}"
        # Return file URL for QML
        
        return file_url
    
    
    @Slot(int, str)
    def updatePreviewContent(self, index, content):
        """Update the preview content for a specific item"""
        item = self._blog_model.getItem(index)
        if item:
            item.previewContent = content
            # Notify the model that this item's data has changed
            model_index = self._blog_model.index(index, 0)
            self._blog_model.dataChanged.emit(model_index, model_index, [self._blog_model.PreviewContentRole])
    
    @Slot(int, str)
    def updateItemImage(self, index, imageName):
        """Update the image for a specific blog item"""
        try:
            item = self._blog_model.getItem(index)
            if item:
                pass
                item.imagePath = imageName
                
                # Notify the model that this item's data has changed
                model_index = self._blog_model.index(index, 0)
                self._blog_model.dataChanged.emit(model_index, model_index, [self._blog_model.ImagePathRole])
                
                self.status = f"Updated image for '{item.title}' to '{imageName}' - hit Update to apply to published blog"
        except Exception as e:
            pass
            self.status = f"Error updating image: {e}"
    
    def _updatePublishedBlogImage(self, item, new_image):
        """Update image for an already published blog"""
        try:
            # Update blog-data.json
            if self._processor.blog_data_path.exists():
                with open(self._processor.blog_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Find and update the post
                for post in data.get("posts", []):
                    if post.get("slug") == item.slug:
                        old_image = post.get("featuredImage", "")
                        post["featuredImage"] = new_image
                        data["lastUpdated"] = datetime.now().isoformat()
                        
                        # Save updated data
                        with open(self._processor.blog_data_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2)
                        
                        # Update blogs.html
                        self._processor.update_blogs_html_image(item.slug, old_image, new_image)
                        
                        # Update individual blog HTML
                        self._processor.update_blog_post_image(item.slug, new_image)
                        
                        break
        except Exception as e:
            pass
    
    @Slot()
    def _onProcessingFinished(self):
        """Handle completion of all processing"""
        self.status = "processing completed - refreshing..."
        self.processingFinished.emit()
        # Signal to preserve current page before refresh
        self.preserveCurrentPage.emit()
        # Refresh the scan to update published status
        self.scanForPdfs()

def main():
    app = QGuiApplication(sys.argv)
    
    # Set style
    QQuickStyle.setStyle("Material")
    
    # Register QML types
    qmlRegisterType(BlogProcessorBackend, "BlogProcessor", 1, 0, "BlogProcessorBackend")
    qmlRegisterType(BlogListModel, "BlogProcessor", 1, 0, "BlogListModel")
    qmlRegisterType(BlogItem, "BlogProcessor", 1, 0, "BlogItem")
    
    # Create and show QML engine
    from PySide6.QtQml import QQmlApplicationEngine
    
    engine = QQmlApplicationEngine()
    
    # Load QML file
    qml_file = Path(__file__).parent / "blog_processor_ui.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    
    if not engine.rootObjects():
        return -1
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())