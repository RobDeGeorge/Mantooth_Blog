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

try:
    from PIL import Image as PILImage
except ImportError:
    print("WARNING: PIL/Pillow not installed. Image details will be limited.")
    PILImage = None

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
        """Generate blog HTML file to match existing blog format"""
        
        # Enhanced template with better SEO, accessibility, and responsive design
        template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{meta_description}">
    <meta name="keywords" content="{meta_keywords}">
    <meta name="author" content="Mantooth">
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://mantooth.com/blog-processor/output/{slug}.html">
    <meta property="og:title" content="{title} - Mantooth">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:image" content="{og_image_url}">
    
    <!-- Twitter -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:url" content="https://mantooth.com/blog-processor/output/{slug}.html">
    <meta property="twitter:title" content="{title} - Mantooth">
    <meta property="twitter:description" content="{meta_description}">
    <meta property="twitter:image" content="{og_image_url}">
    
    <title>{title} - Mantooth</title>
    <link rel="stylesheet" href="../../assets/css/style.css">
    <link rel="canonical" href="https://mantooth.com/blog-processor/output/{slug}.html">
    
    <!-- Structured Data -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": "{title}",
        "description": "{meta_description}",
        "image": "{og_image_url}",
        "author": {{
            "@type": "Person",
            "name": "Mantooth"
        }},
        "publisher": {{
            "@type": "Organization",
            "name": "Mantooth",
            "logo": {{
                "@type": "ImageObject",
                "url": "https://mantooth.com/assets/images/logo.png"
            }}
        }},
        "datePublished": "{iso_date}",
        "dateModified": "{iso_date}",
        "mainEntityOfPage": {{
            "@type": "WebPage",
            "@id": "https://mantooth.com/blog-processor/output/{slug}.html"
        }}
    }}
    </script>
</head>
<body>
    <header role="banner">
        <div class="container">
            <h1 class="logo">Mantooth</h1>
            <nav role="navigation" aria-label="Main navigation">
                <ul>
                    <li><a href="../../index.html">Home</a></li>
                    <li><a href="../../blogs.html" class="active" aria-current="page">Blogs</a></li>
                    <li><a href="../../about.html">About</a></li>
                    <li><a href="../../contact.html">Contact</a></li>
                </ul>
            </nav>
        </div>
    </header>

    <main role="main">
        <div class="container">
            <article class="blog-post" itemscope itemtype="https://schema.org/BlogPosting">
                <h2 class="blog-title">{title}</h2>
                <p class="post-meta">Posted on {formatted_date}</p>
                
{featured_image_html}
                
                <div class="blog-content" itemprop="articleBody">
{content}
                </div>
                
                
                <div class="tags">
{tags_html}
                </div>
            </article>
        </div>
    </main>

    <footer role="contentinfo">
        <div class="container">
            <p>&copy; 2025 Mantooth. All Rights Reserved.</p>
            <div class="social-links">
                <a href="#" aria-label="Facebook">Facebook</a>
                <a href="#" aria-label="Instagram">Instagram</a>
            </div>
        </div>
    </footer>

    <script src="../../assets/js/image-optimizer.js"></script>
    <script src="../../assets/js/clickable-cards.js"></script>
    <script>
        // Share functionality
        function shareArticle() {{
            if (navigator.share) {{
                navigator.share({{
                    title: '{title}',
                    text: '{meta_description}',
                    url: window.location.href
                }});
            }} else {{
                // Fallback: copy URL to clipboard
                navigator.clipboard.writeText(window.location.href).then(() => {{
                    alert('Article URL copied to clipboard!');
                }});
            }}
        }}
        
        // Enhanced analytics tracking
        document.addEventListener('DOMContentLoaded', function() {{
            // Track article view
            if (typeof gtag !== 'undefined') {{
                gtag('event', 'page_view', {{
                    'article_title': '{title}',
                    'article_tags': '{meta_keywords}'
                }});
            }}
            
            // Track reading progress
            let readingProgress = 0;
            const article = document.querySelector('.blog-content');
            const articleHeight = article.offsetHeight;
            
            window.addEventListener('scroll', function() {{
                const scrollTop = window.pageYOffset;
                const articleTop = article.offsetTop;
                const progress = Math.min(100, Math.max(0, 
                    ((scrollTop - articleTop + window.innerHeight) / articleHeight) * 100
                ));
                
                if (progress > readingProgress + 25) {{
                    readingProgress = Math.floor(progress / 25) * 25;
                    if (typeof gtag !== 'undefined') {{
                        gtag('event', 'scroll', {{
                            'event_category': 'Reading Progress',
                            'event_label': '{title}',
                            'value': readingProgress
                        }});
                    }}
                }}
            }});
        }});
    </script>
</body>
</html>'''
        
        # Enhanced tag HTML with semantic markup
        tags_html = '\n'.join([
            f'                        <span class="tag" role="listitem" itemprop="keywords">{self.escape_html(tag.title())}</span>' 
            for tag in blog_data['tags']
        ])
        
        # Enhanced image HTML with better accessibility and lazy loading
        featured_image = blog_data.get('featured_image', '')
        if featured_image and featured_image.strip():
            alt_text = f"Featured image for {blog_data['title']}"
            featured_image_html = f'''                <img data-src="../images/{featured_image}" alt="{self.escape_html(alt_text)}" class="blog-featured-image lazy-loading">'''
        else:
            featured_image_html = '                <!-- No featured image -->'
        
        # Generate meta description from excerpt
        meta_description = self.escape_html(blog_data.get('excerpt', '')[:160])
        meta_keywords = ', '.join([tag.lower() for tag in blog_data['tags']])
        
        # Generate Open Graph image URL
        if featured_image:
            og_image_url = f"https://mantooth.com/blog-processor/images/{featured_image}"
        else:
            og_image_url = "https://mantooth.com/assets/images/default-og-image.png"
        
        # Convert date to ISO format
        try:
            from datetime import datetime
            iso_date = datetime.strptime(blog_data.get('publish_date', '2025-01-01'), '%Y-%m-%d').isoformat()
        except:
            iso_date = '2025-01-01T00:00:00'
        
        # Calculate reading time (average 200 words per minute)
        content_text = re.sub(r'<[^>]+>', '', blog_data.get('content', ''))
        word_count = len(content_text.split())
        reading_time = max(1, round(word_count / 200))
        
        return template.format(
            title=self.escape_html(blog_data['title']),
            slug=blog_data.get('slug', ''),
            formatted_date=blog_data['formatted_date'],
            iso_date=iso_date,
            reading_time=reading_time,
            featured_image_html=featured_image_html,
            content=blog_data['content'],  # Already HTML
            tags_html=tags_html,
            meta_description=meta_description,
            meta_keywords=meta_keywords,
            og_image_url=og_image_url
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
    """Enhanced background thread for PDF processing with cancellation and progress"""
    
    progressUpdate = Signal(int, str)  # index, status
    itemProcessed = Signal(int, dict)  # index, blog_data
    finished = Signal()
    progressChanged = Signal(int, int, str)  # current, total, current_task
    errorOccurred = Signal(str, str)  # error_message, suggested_action
    
    def __init__(self, processor: BlogProcessor, items: List[BlogItem]):
        super().__init__()
        self.processor = processor
        self.items = items
        self._cancelled = False
        self._current_task = ""
        
    def cancel(self):
        """Cancel the processing"""
        self._cancelled = True
        
    def run(self):
        total_items = len(self.items)
        
        try:
            for i, item in enumerate(self.items):
                if self._cancelled:
                    break
                    
                try:
                    self._current_task = f"Processing {item.title}"
                    self.progressChanged.emit(i + 1, total_items, self._current_task)
                    self.progressUpdate.emit(i, "processing")
                    
                    # Check if thread should stop
                    if self._cancelled:
                        break
                    
                    # Extract text from PDF with progress updates
                    self._current_task = f"Extracting text from {item.title}"
                    self.progressChanged.emit(i + 1, total_items, self._current_task)
                    
                    pdf_path = Path(item.pdfPath)
                    extraction_result = self.processor.extract_text_from_pdf(pdf_path)
                    
                    if not extraction_result:
                        self.progressUpdate.emit(i, "error")
                        self.errorOccurred.emit(
                            f"Failed to extract text from {pdf_path.name}",
                            "Check if the PDF is valid and not corrupted"
                        )
                        continue
                    
                    if self._cancelled:
                        break
                    
                    paragraphs = extraction_result['paragraphs']
                    
                    # Use edited preview content if available, otherwise use extracted paragraphs
                    if item.previewContent.strip():
                        self._current_task = f"Processing edited content for {item.title}"
                        self.progressChanged.emit(i + 1, total_items, self._current_task)
                        paragraphs = self.processor.parse_preview_content(item.previewContent)
                    
                    if self._cancelled:
                        break
                    
                    # Generate blog data with progress updates
                    self._current_task = f"Generating HTML for {item.title}"
                    self.progressChanged.emit(i + 1, total_items, self._current_task)
                    
                    title = item.title if item.title else self.processor.extract_title_from_filename(pdf_path.name)
                    slug = self.processor.generate_slug(title)
                    content_html = self.processor.format_content_to_html(paragraphs, title)
                    excerpt = self.processor.generate_excerpt(paragraphs)
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
                        'edited_content': item.previewContent,
                        'processing_time': time.time()
                    }
                    
                    if self._cancelled:
                        break
                    
                    self.itemProcessed.emit(i, blog_data)
                    self.progressUpdate.emit(i, "completed")
                    
                    # Small delay to prevent UI freezing
                    self.msleep(100)
                    
                except Exception as e:
                    error_msg = f"Error processing {item.title if item else 'unknown'}: {str(e)}"
                    self.errorOccurred.emit(error_msg, "Check the PDF file and try again")
                    self.progressUpdate.emit(i, "error")
                    continue
        
        except Exception as e:
            self.errorOccurred.emit(f"Critical processing error: {str(e)}", "Restart the application")
        
        finally:
            if self._cancelled:
                self.progressChanged.emit(0, total_items, "Processing cancelled")
            else:
                self.progressChanged.emit(total_items, total_items, "Processing completed")
            self.finished.emit()

@QmlElement
class BlogProcessorBackend(QObject):
    """Main backend controller for the blog processor UI"""
    
    statusChanged = Signal(str)
    progressChanged = Signal(int, int)  # current, total
    itemsChanged = Signal()
    processingFinished = Signal()
    preserveCurrentPage = Signal()
    realTimeUpdateSignal = Signal(int, str, str)  # index, property, value
    dataValidationSignal = Signal(str, bool)  # message, isError
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._status = "ready"
        self._processor = BlogProcessor()
        self._blog_manager = BlogManager()
        self._blog_model = BlogListModel()
        self._processing_thread = None
        self._auto_save_timers = {}  # Track auto-save timers per item
        self._debounce_delay = 3000  # 3 seconds debounce for auto-save
        
        # Performance optimizations
        self._content_cache = {}  # Cache extracted content
        self._image_cache = {}   # Cache image paths
        self._last_scan_time = 0 # Track last scan to avoid excessive rescans
        self._scan_debounce_timer = None
        
        # Background task queue
        self._task_queue = []
        self._background_worker = None
        
        # Memory management
        self._max_cache_size = 50  # Maximum items in cache
        self._max_content_length = 100000  # Maximum content length to cache
        
        # Lazy loading
        self._lazy_load_enabled = True
        self._load_queue = []
        
        # Cleanup timer for memory management
        from PySide6.QtCore import QTimer
        self._cleanup_timer = QTimer()
        self._cleanup_timer.timeout.connect(self._performMemoryCleanup)
        self._cleanup_timer.start(60000)  # Clean up every minute
        
        # Auto-backup timer
        self._auto_backup_timer = QTimer()
        self._auto_backup_timer.timeout.connect(self._performAutoBackup)
        self._auto_backup_timer.start(1800000)  # Auto-backup every 30 minutes
        
        # Data validation
        self._last_validation_time = 0
        self._validation_interval = 300  # Validate every 5 minutes
    
    def _performAutoBackup(self):
        """Perform automatic backup if there are changes"""
        try:
            # Only backup if there are published blogs
            published_count = len([item for item in range(self._blog_model.rowCount()) 
                                 if self._blog_model.getItem(item) and 
                                 self._blog_model.getItem(item).status == "published"])
            
            if published_count > 0:
                self.createBackup()
                
        except Exception:
            pass  # Silent failure for auto-backup
    
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
        """Optimized PDF scanning with caching and debouncing"""
        current_time = time.time()
        
        # Debounce rapid scan requests
        if current_time - self._last_scan_time < 2.0:  # 2 second debounce
            if self._scan_debounce_timer:
                self._scan_debounce_timer.stop()
            
            from PySide6.QtCore import QTimer
            self._scan_debounce_timer = QTimer()
            self._scan_debounce_timer.setSingleShot(True)
            self._scan_debounce_timer.timeout.connect(self._performScan)
            self._scan_debounce_timer.start(500)
            return
        
        self._performScan()
    
    def _performScan(self):
        """Perform the actual PDF scan with optimizations"""
        self.status = "🔄 Scanning and loading content..."
        self._blog_model.clear()
        self._last_scan_time = time.time()
        
        try:
            pdfs = self._processor.list_available_pdfs()
            published_data = self._blog_manager.get_existing_blogs()
            published_posts = {post.get("slug", ""): post for post in published_data.get("posts", [])}
            
            # Process PDFs in chunks to prevent UI freezing
            chunk_size = 3
            total_pdfs = len(pdfs)
            
            for chunk_start in range(0, total_pdfs, chunk_size):
                chunk_end = min(chunk_start + chunk_size, total_pdfs)
                chunk_pdfs = pdfs[chunk_start:chunk_end]
                
                self.status = f"📄 Processing PDFs {chunk_start + 1}-{chunk_end} of {total_pdfs}..."
                
                for pdf_path in chunk_pdfs:
                    item = self._createBlogItemFromPdf(pdf_path, published_posts)
                    if item:
                        self._blog_model.addItem(item)
                
                # Allow UI to update between chunks
                QGuiApplication.processEvents()
            
            published_count = len([item for item in range(self._blog_model.rowCount()) 
                                 if self._blog_model.getItem(item).status == "published"])
            
            self.status = f"✅ Loaded {len(pdfs)} PDFs ({published_count} published)"
            self.itemsChanged.emit()
            
        except Exception as e:
            self.status = f"❌ Scan error: {e}"
            self.dataValidationSignal.emit(f"Failed to scan PDFs: {e}", True)
    
    def _createBlogItemFromPdf(self, pdf_path: Path, published_posts: dict) -> Optional[BlogItem]:
        """Create a blog item from PDF with caching"""
        try:
            item = BlogItem(str(pdf_path))
            
            # Extract basic info
            title = self._processor.extract_title_from_filename(pdf_path.name)
            slug = self._processor.generate_slug(title)
            
            # Check cache first
            cache_key = f"{pdf_path.name}_{pdf_path.stat().st_mtime}"
            if cache_key in self._content_cache:
                cached_data = self._content_cache[cache_key]
                preview_content = cached_data['preview_content']
                excerpt = cached_data['excerpt']
            else:
                # Extract content
                try:
                    extraction_result = self._processor.extract_text_from_pdf(pdf_path)
                    if extraction_result:
                        paragraphs = extraction_result['paragraphs']
                        preview_lines = [para.strip() for para in paragraphs if para.strip()]
                        preview_content = '\n\n'.join(preview_lines)
                        excerpt = self._processor.generate_excerpt(paragraphs)
                        
                        # Cache the result
                        self._content_cache[cache_key] = {
                            'preview_content': preview_content,
                            'excerpt': excerpt,
                            'paragraphs': paragraphs
                        }
                    else:
                        preview_content = ""
                        excerpt = "Failed to extract content from PDF"
                except Exception as e:
                    preview_content = ""
                    excerpt = f"Error loading PDF: {str(e)}"
            
            # Check if already published and get existing data
            if slug in published_posts:
                published_post = published_posts[slug]
                source_file_matches = published_post.get("sourceFile", "") == pdf_path.name
                
                item.title = published_post.get("title", title)
                item.tags = published_post.get("tags", []) if source_file_matches else []
                item.status = "published"
                item.excerpt = published_post.get("excerpt", excerpt)
                item.imagePath = published_post.get("featuredImage", "")
                
                saved_content = published_post.get("editedContent", "")
                item.previewContent = saved_content if saved_content else preview_content
            else:
                item.title = title
                item.tags = []
                item.status = "pending"
                item.excerpt = excerpt
                item.imagePath = ""
                item.previewContent = preview_content
            
            item.slug = slug
            return item
            
        except Exception as e:
            self.dataValidationSignal.emit(f"Failed to process {pdf_path.name}: {e}", True)
            return None
    
    @Slot(int, str)
    def updateItemTags(self, index: int, tags_string: str):
        """Update tags for a specific item with validation"""
        item = self._blog_model.getItem(index)
        if item:
            # Enhanced tag validation
            tags_list = [tag.strip().lower() for tag in tags_string.split(',') if tag.strip()]
            
            # Validate tags
            validation_result = self.validateTags(tags_list)
            if not validation_result["valid"]:
                self.dataValidationSignal.emit(validation_result["message"], True)
                return
            
            # Apply validated tags
            item.tags = tags_list
            
            # Emit real-time update signal
            self.realTimeUpdateSignal.emit(index, "tags", tags_string)
            
            # Notify the model that this item's data has changed
            model_index = self._blog_model.index(index, 0)
            self._blog_model.dataChanged.emit(model_index, model_index, [self._blog_model.TagsRole])
            
            # Auto-save if published
            if item.status == "published":
                self._autoSaveItemData(index)
    
    def validateTags(self, tags_list: List[str]) -> Dict[str, any]:
        """Validate tags according to rules"""
        if len(tags_list) == 0:
            return {"valid": False, "message": "At least one tag is required"}
        
        if len(tags_list) > 8:
            return {"valid": False, "message": "Maximum 8 tags allowed"}
        
        for tag in tags_list:
            if len(tag) > 20:
                return {"valid": False, "message": f"Tag '{tag}' too long (max 20 characters)"}
            
            if not tag.replace('-', '').replace('_', '').isalnum():
                return {"valid": False, "message": f"Tag '{tag}' contains invalid characters"}
        
        return {"valid": True, "message": "Tags are valid"}
    
    @Slot(int, str)
    def updateItemTitle(self, index: int, new_title: str):
        """Update title for a specific item with validation"""
        item = self._blog_model.getItem(index)
        if item:
            # Validate title
            cleaned_title = new_title.strip()
            if len(cleaned_title) == 0:
                self.dataValidationSignal.emit("Title cannot be empty", True)
                return
            
            if len(cleaned_title) > 100:
                self.dataValidationSignal.emit("Title too long (max 100 characters)", True)
                return
            
            item.title = cleaned_title
            
            # Emit real-time update signal
            self.realTimeUpdateSignal.emit(index, "title", cleaned_title)
            
            # Notify the model that this item's data has changed
            model_index = self._blog_model.index(index, 0)
            self._blog_model.dataChanged.emit(model_index, model_index, [self._blog_model.TitleRole])
            
            # Auto-save if published
            if item.status == "published":
                self._autoSaveItemData(index)
    
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
        """Process a single item by index with enhanced error handling"""
        if self._processing_thread and self._processing_thread.isRunning():
            self.dataValidationSignal.emit("Processing already in progress. Please wait or cancel current operation.", True)
            return
        
        item = self._blog_model.getItem(index)
        if not item:
            self.dataValidationSignal.emit("Invalid blog item selected", True)
            return
            
        if item.status == "published":
            self.dataValidationSignal.emit("Blog is already published. Use 'Update' instead.", True)
            return
            
        if not item.tags or len(item.tags) == 0:
            self.dataValidationSignal.emit("Please add tags before processing", True)
            return
        
        self.status = f"⚙️ Processing {item.title}..."
        self._processing_thread = ProcessingThread(self._processor, [item])
        
        # Connect enhanced signals
        self._processing_thread.progressUpdate.connect(self._onProgressUpdate)
        self._processing_thread.itemProcessed.connect(self._onItemProcessed)
        self._processing_thread.finished.connect(self._onProcessingFinished)
        self._processing_thread.progressChanged.connect(self._onDetailedProgress)
        self._processing_thread.errorOccurred.connect(self._onProcessingError)
        
        self._processing_thread.start()
    
    @Slot(int, int, str)
    def _onDetailedProgress(self, current: int, total: int, task: str):
        """Handle detailed progress updates"""
        self.status = f"⚙️ [{current}/{total}] {task}"
        self.progressChanged.emit(current, total)
    
    @Slot(str, str)
    def _onProcessingError(self, error_message: str, suggested_action: str):
        """Handle processing errors with suggestions"""
        self.dataValidationSignal.emit(f"{error_message}. {suggested_action}", True)
    
    @Slot()
    def cancelProcessing(self):
        """Cancel current processing operation"""
        if self._processing_thread and self._processing_thread.isRunning():
            self._processing_thread.cancel()
            self.status = "🛑 Cancelling processing..."
        else:
            self.dataValidationSignal.emit("No processing operation to cancel", False)
    
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
        """Get list of available images with caching"""
        try:
            # Check cache first
            cache_key = "available_images"
            current_time = time.time()
            
            if cache_key in self._image_cache:
                cached_data = self._image_cache[cache_key]
                # Cache for 30 seconds
                if current_time - cached_data['timestamp'] < 30:
                    return cached_data['images']
            
            # Get fresh data
            available_images = self._processor.list_available_images()
            
            # Cache the result
            self._image_cache[cache_key] = {
                'images': available_images,
                'timestamp': current_time
            }
            
            return available_images
        except Exception as e:
            self.dataValidationSignal.emit(f"Error loading images: {e}", True)
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
        
        # Check if file exists, return placeholder if not
        if not full_path.exists():
            return ""
        
        file_url = f"file://{full_path}"
        return file_url
    
    @Slot(result=list)
    def getImageFormats(self):
        """Get supported image formats"""
        return [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"]
    
    @Slot(str, result=dict)
    def getImageDetails(self, imageName):
        """Get detailed information about an image file"""
        try:
            if not imageName:
                return {}
            
            image_path = self._processor.blog_images_dir / imageName
            if not image_path.exists():
                return {}
            
            import os
            from PIL import Image as PILImage
            
            stat = os.stat(image_path)
            
            # Get image dimensions
            try:
                with PILImage.open(image_path) as img:
                    width, height = img.size
                    format_name = img.format
            except Exception:
                width = height = 0
                format_name = "Unknown"
            
            return {
                "name": imageName,
                "size": stat.st_size,
                "width": width,
                "height": height,
                "format": format_name,
                "modified": stat.st_mtime
            }
            
        except Exception:
            return {}
    
    def _performMemoryCleanup(self):
        """Perform periodic memory cleanup"""
        try:
            current_time = time.time()
            
            # Clean content cache if it's too large
            if len(self._content_cache) > self._max_cache_size:
                # Remove oldest entries
                cache_items = list(self._content_cache.items())
                # Sort by access time if available, otherwise remove randomly
                cache_items.sort(key=lambda x: x[1].get('last_access', 0))
                
                # Keep only the most recent half
                keep_count = self._max_cache_size // 2
                self._content_cache = dict(cache_items[-keep_count:])
            
            # Clean image cache (older than 5 minutes)
            expired_keys = []
            for key, cached_data in self._image_cache.items():
                if current_time - cached_data.get('timestamp', 0) > 300:  # 5 minutes
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._image_cache[key]
            
            # Clean up auto-save timers for non-existent items
            valid_indices = set(range(self._blog_model.rowCount()))
            expired_timers = []
            for index, timer in self._auto_save_timers.items():
                if index not in valid_indices:
                    if timer:
                        timer.stop()
                    expired_timers.append(index)
            
            for index in expired_timers:
                del self._auto_save_timers[index]
                
        except Exception as e:
            # Silent cleanup failure - don't disrupt user experience
            pass
    
    @Slot(int)
    def lazyLoadContent(self, index: int):
        """Lazy load content for a specific item"""
        if not self._lazy_load_enabled:
            return
            
        try:
            item = self._blog_model.getItem(index)
            if not item:
                return
            
            # Check if content needs loading
            if not item.previewContent or len(item.previewContent.strip()) == 0:
                # Add to load queue
                if index not in self._load_queue:
                    self._load_queue.append(index)
                    
                    # Process queue with delay to batch requests
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(100, self._processLoadQueue)
                    
        except Exception as e:
            pass
    
    def _processLoadQueue(self):
        """Process the lazy loading queue"""
        if not self._load_queue:
            return
            
        try:
            # Process up to 3 items at once
            batch_size = min(3, len(self._load_queue))
            current_batch = self._load_queue[:batch_size]
            self._load_queue = self._load_queue[batch_size:]
            
            for index in current_batch:
                item = self._blog_model.getItem(index)
                if item and item.pdfPath:
                    pdf_path = Path(item.pdfPath)
                    
                    # Check cache first
                    cache_key = f"{pdf_path.name}_{pdf_path.stat().st_mtime}"
                    if cache_key not in self._content_cache:
                        # Load in background
                        self._loadContentInBackground(index, pdf_path, cache_key)
                        
        except Exception as e:
            pass
    
    def _loadContentInBackground(self, index: int, pdf_path: Path, cache_key: str):
        """Load content in background thread"""
        try:
            # Use a simple thread for content loading
            from PySide6.QtCore import QThread, QObject, Signal
            
            class ContentLoader(QObject):
                contentLoaded = Signal(int, str, str)  # index, content, excerpt
                
                def __init__(self, processor, pdf_path, parent=None):
                    super().__init__(parent)
                    self.processor = processor
                    self.pdf_path = pdf_path
                
                def load(self):
                    try:
                        extraction_result = self.processor.extract_text_from_pdf(self.pdf_path)
                        if extraction_result:
                            paragraphs = extraction_result['paragraphs']
                            preview_lines = [para.strip() for para in paragraphs if para.strip()]
                            preview_content = '\n\n'.join(preview_lines)
                            excerpt = self.processor.generate_excerpt(paragraphs)
                            
                            # Limit content length for memory efficiency
                            if len(preview_content) > self._max_content_length:
                                preview_content = preview_content[:self._max_content_length] + "\n\n[Content truncated for performance]"
                            
                            return preview_content, excerpt
                    except Exception:
                        pass
                    return "", "Failed to load content"
            
            # For now, load synchronously but with content limits
            # In a full implementation, this would use a proper worker thread
            loader = ContentLoader(self._processor, pdf_path)
            preview_content, excerpt = loader.load()
            
            # Update the item
            item = self._blog_model.getItem(index)
            if item:
                item.previewContent = preview_content
                item.excerpt = excerpt
                
                # Cache the result
                self._content_cache[cache_key] = {
                    'preview_content': preview_content,
                    'excerpt': excerpt,
                    'last_access': time.time()
                }
                
                # Notify model of changes
                model_index = self._blog_model.index(index, 0)
                self._blog_model.dataChanged.emit(model_index, model_index, 
                    [self._blog_model.PreviewContentRole, self._blog_model.ExcerptRole])
                
        except Exception as e:
            pass
    
    @Slot(bool)
    def setLazyLoadingEnabled(self, enabled: bool):
        """Enable or disable lazy loading"""
        self._lazy_load_enabled = enabled
    
    @Slot(result=dict)
    def getMemoryUsage(self):
        """Get current memory usage statistics"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            return {
                "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                "content_cache_size": len(self._content_cache),
                "image_cache_size": len(self._image_cache),
                "auto_save_timers": len(self._auto_save_timers)
            }
        except Exception:
            return {
                "content_cache_size": len(self._content_cache),
                "image_cache_size": len(self._image_cache),
                "auto_save_timers": len(self._auto_save_timers)
            }
    
    @Slot()
    def clearCache(self):
        """Manually clear all caches"""
        try:
            self._content_cache.clear()
            self._image_cache.clear()
            
            # Stop and clear auto-save timers
            for timer in self._auto_save_timers.values():
                if timer:
                    timer.stop()
            self._auto_save_timers.clear()
            
            self.status = "🗑️ Cache cleared"
            
        except Exception as e:
            self.dataValidationSignal.emit(f"Failed to clear cache: {e}", True)
    
    @Slot(result=bool)
    def createBackup(self):
        """Create a backup of all blog data and files"""
        try:
            import shutil
            from datetime import datetime
            
            # Create backup directory with timestamp
            backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self._processor.project_root / "backups" / f"blog_backup_{backup_time}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup JSON data
            if self._processor.blog_data_path.exists():
                shutil.copy2(self._processor.blog_data_path, backup_dir / "blog-data.json")
            
            # Backup blogs.html
            if self._processor.blogs_html_path.exists():
                shutil.copy2(self._processor.blogs_html_path, backup_dir / "blogs.html")
            
            # Backup all generated HTML files
            html_backup_dir = backup_dir / "output"
            html_backup_dir.mkdir(exist_ok=True)
            
            for html_file in self._processor.blogs_dir.glob("*.html"):
                shutil.copy2(html_file, html_backup_dir / html_file.name)
            
            # Backup images
            images_backup_dir = backup_dir / "images"
            images_backup_dir.mkdir(exist_ok=True)
            
            for image_file in self._processor.blog_images_dir.glob("*"):
                if image_file.is_file():
                    shutil.copy2(image_file, images_backup_dir / image_file.name)
            
            # Create backup manifest
            manifest = {
                "backup_time": backup_time,
                "backup_date": datetime.now().isoformat(),
                "total_blogs": self._blog_model.rowCount(),
                "files_backed_up": {
                    "json_data": self._processor.blog_data_path.exists(),
                    "blogs_html": self._processor.blogs_html_path.exists(),
                    "html_files": len(list(self._processor.blogs_dir.glob("*.html"))),
                    "image_files": len(list(self._processor.blog_images_dir.glob("*")))
                },
                "backup_size_mb": self._get_directory_size(backup_dir) / (1024 * 1024)
            }
            
            with open(backup_dir / "backup_manifest.json", 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)
            
            self.status = f"✅ Backup created: {backup_dir.name}"
            self.dataValidationSignal.emit(f"Backup successfully created in {backup_dir}", False)
            
            # Clean up old backups (keep last 10)
            self._cleanupOldBackups()
            
            return True
            
        except Exception as e:
            self.dataValidationSignal.emit(f"Failed to create backup: {e}", True)
            return False
    
    def _get_directory_size(self, directory: Path) -> int:
        """Calculate total size of directory in bytes"""
        total_size = 0
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception:
            pass
        return total_size
    
    def _cleanupOldBackups(self):
        """Clean up old backup directories, keeping only the latest 10"""
        try:
            backups_dir = self._processor.project_root / "backups"
            if not backups_dir.exists():
                return
            
            # Get all backup directories
            backup_dirs = [d for d in backups_dir.iterdir() if d.is_dir() and d.name.startswith("blog_backup_")]
            
            # Sort by creation time (newest first)
            backup_dirs.sort(key=lambda x: x.stat().st_ctime, reverse=True)
            
            # Remove old backups (keep only 10 most recent)
            for old_backup in backup_dirs[10:]:
                shutil.rmtree(old_backup)
                
        except Exception:
            pass
    
    @Slot(result=list)
    def getAvailableBackups(self):
        """Get list of available backups"""
        try:
            backups_dir = self._processor.project_root / "backups"
            if not backups_dir.exists():
                return []
            
            backups = []
            for backup_dir in backups_dir.iterdir():
                if backup_dir.is_dir() and backup_dir.name.startswith("blog_backup_"):
                    manifest_path = backup_dir / "backup_manifest.json"
                    if manifest_path.exists():
                        try:
                            with open(manifest_path, 'r', encoding='utf-8') as f:
                                manifest = json.load(f)
                            
                            backup_info = {
                                "name": backup_dir.name,
                                "path": str(backup_dir),
                                "date": manifest.get("backup_date", ""),
                                "size_mb": round(manifest.get("backup_size_mb", 0), 2),
                                "total_blogs": manifest.get("total_blogs", 0),
                                "files": manifest.get("files_backed_up", {})
                            }
                            backups.append(backup_info)
                        except:
                            # Invalid manifest, skip this backup
                            continue
            
            # Sort by date (newest first)
            backups.sort(key=lambda x: x["date"], reverse=True)
            return backups
            
        except Exception as e:
            self.dataValidationSignal.emit(f"Failed to list backups: {e}", True)
            return []
    
    @Slot(str, result=bool)
    def restoreFromBackup(self, backup_name: str):
        """Restore data from a specific backup"""
        try:
            import shutil
            
            backup_dir = self._processor.project_root / "backups" / backup_name
            if not backup_dir.exists():
                self.dataValidationSignal.emit(f"Backup {backup_name} not found", True)
                return False
            
            # Create a backup of current state before restoring
            self.createBackup()
            
            # Restore JSON data
            backup_json = backup_dir / "blog-data.json"
            if backup_json.exists():
                shutil.copy2(backup_json, self._processor.blog_data_path)
            
            # Restore blogs.html
            backup_html = backup_dir / "blogs.html"
            if backup_html.exists():
                shutil.copy2(backup_html, self._processor.blogs_html_path)
            
            # Restore HTML files
            backup_output = backup_dir / "output"
            if backup_output.exists():
                # Clear existing HTML files
                for existing_html in self._processor.blogs_dir.glob("*.html"):
                    existing_html.unlink()
                
                # Copy backup HTML files
                for backup_html_file in backup_output.glob("*.html"):
                    shutil.copy2(backup_html_file, self._processor.blogs_dir / backup_html_file.name)
            
            # Restore images (optional - might want to preserve newer images)
            backup_images = backup_dir / "images"
            if backup_images.exists():
                for backup_image in backup_images.glob("*"):
                    if backup_image.is_file():
                        dest_path = self._processor.blog_images_dir / backup_image.name
                        if not dest_path.exists():  # Only restore if image doesn't exist
                            shutil.copy2(backup_image, dest_path)
            
            self.status = f"✅ Restored from backup: {backup_name}"
            self.dataValidationSignal.emit(f"Successfully restored from {backup_name}", False)
            
            # Refresh the blog list
            self.scanForPdfs()
            
            return True
            
        except Exception as e:
            self.dataValidationSignal.emit(f"Failed to restore from backup: {e}", True)
            return False
    
    @Slot(result=bool)
    def validateAllData(self):
        """Comprehensive data validation"""
        try:
            validation_errors = []
            
            # Validate JSON structure
            try:
                if self._processor.blog_data_path.exists():
                    with open(self._processor.blog_data_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if "posts" not in data:
                        validation_errors.append("blog-data.json missing 'posts' field")
                    
                    if "totalPosts" not in data:
                        validation_errors.append("blog-data.json missing 'totalPosts' field")
                    
                    # Validate each post
                    for i, post in enumerate(data.get("posts", [])):
                        required_fields = ["title", "slug", "publishDate", "tags"]
                        for field in required_fields:
                            if field not in post:
                                validation_errors.append(f"Post {i+1} missing '{field}' field")
                        
                        # Validate slug format
                        slug = post.get("slug", "")
                        if slug and not re.match(r'^[a-z0-9-]+$', slug):
                            validation_errors.append(f"Post '{post.get('title', '')}' has invalid slug format")
                        
                        # Check if HTML file exists
                        html_file = self._processor.blogs_dir / f"{slug}.html"
                        if not html_file.exists():
                            validation_errors.append(f"HTML file missing for '{post.get('title', '')}'")
                        
                        # Check if featured image exists
                        featured_image = post.get("featuredImage", "")
                        if featured_image:
                            image_path = self._processor.blog_images_dir / featured_image
                            if not image_path.exists():
                                validation_errors.append(f"Featured image missing: {featured_image}")
                else:
                    validation_errors.append("blog-data.json file does not exist")
                    
            except json.JSONDecodeError as e:
                validation_errors.append(f"blog-data.json is invalid JSON: {e}")
            
            # Validate blogs.html
            if self._processor.blogs_html_path.exists():
                with open(self._processor.blogs_html_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                required_elements = [
                    '<section class="blogs-grid">',
                    'clickable-cards.js',
                    'image-optimizer.js'
                ]
                
                for element in required_elements:
                    if element not in content:
                        validation_errors.append(f"blogs.html missing: {element}")
            else:
                validation_errors.append("blogs.html file does not exist")
            
            # Validate model consistency
            model_count = self._blog_model.rowCount()
            if self._processor.blog_data_path.exists():
                with open(self._processor.blog_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                json_count = len(data.get("posts", []))
                
                published_model_count = len([item for item in range(model_count) 
                                            if self._blog_model.getItem(item) and 
                                            self._blog_model.getItem(item).status == "published"])
                
                if published_model_count != json_count:
                    validation_errors.append(f"Published blog count mismatch: UI shows {published_model_count}, JSON has {json_count}")
            
            # Report results
            if validation_errors:
                error_msg = "\n".join([f"• {error}" for error in validation_errors[:10]])  # Limit to 10 errors
                if len(validation_errors) > 10:
                    error_msg += f"\n... and {len(validation_errors) - 10} more errors"
                
                self.dataValidationSignal.emit(f"Validation failed:\n{error_msg}", True)
                return False
            else:
                self.dataValidationSignal.emit("✅ All data validation checks passed", False)
                return True
                
        except Exception as e:
            self.dataValidationSignal.emit(f"Validation error: {e}", True)
            return False
    
    @Slot(result=bool)
    def repairDataInconsistencies(self):
        """Attempt to repair common data inconsistencies"""
        try:
            repair_actions = []
            
            # Ensure directories exist
            directories = [
                self._processor.blogs_dir,
                self._processor.blog_images_dir,
                self._processor.json_dir
            ]
            
            for directory in directories:
                if not directory.exists():
                    directory.mkdir(parents=True, exist_ok=True)
                    repair_actions.append(f"Created missing directory: {directory}")
            
            # Ensure blog-data.json exists with proper structure
            if not self._processor.blog_data_path.exists():
                empty_data = {
                    "posts": [],
                    "lastUpdated": datetime.now().isoformat(),
                    "totalPosts": 0
                }
                with open(self._processor.blog_data_path, 'w', encoding='utf-8') as f:
                    json.dump(empty_data, f, indent=2)
                repair_actions.append("Created missing blog-data.json")
            
            # Rebuild blogs.html if missing or corrupted
            rebuild_needed = False
            if not self._processor.blogs_html_path.exists():
                rebuild_needed = True
                repair_actions.append("blogs.html was missing")
            else:
                try:
                    with open(self._processor.blogs_html_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if '<section class="blogs-grid">' not in content:
                        rebuild_needed = True
                        repair_actions.append("blogs.html was corrupted")
                except Exception:
                    rebuild_needed = True
                    repair_actions.append("blogs.html was unreadable")
            
            if rebuild_needed:
                self._blog_manager.rebuild_blogs_html()
                repair_actions.append("Rebuilt blogs.html")
            
            # Sync published status with JSON data
            try:
                if self._processor.blog_data_path.exists():
                    with open(self._processor.blog_data_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    published_slugs = {post.get("slug", "") for post in data.get("posts", [])}
                    
                    synced_count = 0
                    for i in range(self._blog_model.rowCount()):
                        item = self._blog_model.getItem(i)
                        if item:
                            if item.slug in published_slugs and item.status != "published":
                                item.status = "published"
                                synced_count += 1
                            elif item.slug not in published_slugs and item.status == "published":
                                item.status = "pending"
                                synced_count += 1
                    
                    if synced_count > 0:
                        repair_actions.append(f"Synced status for {synced_count} items")
            except Exception:
                repair_actions.append("Could not sync published status")
            
            # Report repair actions
            if repair_actions:
                action_msg = "\n".join([f"• {action}" for action in repair_actions])
                self.dataValidationSignal.emit(f"Repairs completed:\n{action_msg}", False)
                
                # Refresh to show changes
                self.scanForPdfs()
            else:
                self.dataValidationSignal.emit("✅ No repairs needed - data is consistent", False)
            
            return True
            
        except Exception as e:
            self.dataValidationSignal.emit(f"Repair failed: {e}", True)
            return False
    
    
    @Slot(int, str)
    def updatePreviewContent(self, index, content):
        """Update the preview content for a specific item with validation"""
        item = self._blog_model.getItem(index)
        if item:
            # Validate content length
            if len(content) > 50000:  # 50KB limit
                self.dataValidationSignal.emit("Content too long (max 50,000 characters)", True)
                return
            
            item.previewContent = content
            
            # Emit real-time update signal (truncated for performance)
            content_preview = content[:100] + "..." if len(content) > 100 else content
            self.realTimeUpdateSignal.emit(index, "content", content_preview)
            
            # Notify the model that this item's data has changed
            model_index = self._blog_model.index(index, 0)
            self._blog_model.dataChanged.emit(model_index, model_index, [self._blog_model.PreviewContentRole])
            
            # Auto-save if published (debounced)
            if item.status == "published":
                self._scheduleAutoSave(index)
    
    @Slot(int, str)
    def updateItemImage(self, index, imageName):
        """Update the image for a specific blog item"""
        try:
            item = self._blog_model.getItem(index)
            if item:
                # Validate image exists
                image_path = self._processor.blog_images_dir / imageName
                if not image_path.exists():
                    self.dataValidationSignal.emit(f"Image '{imageName}' not found", True)
                    return
                
                item.imagePath = imageName
                
                # Emit real-time update signal
                self.realTimeUpdateSignal.emit(index, "image", imageName)
                
                # Notify the model that this item's data has changed
                model_index = self._blog_model.index(index, 0)
                self._blog_model.dataChanged.emit(model_index, model_index, [self._blog_model.ImagePathRole])
                
                self.status = f"✅ Updated image for '{item.title}' to '{imageName}'"
                
                # Auto-save if published
                if item.status == "published":
                    self._autoSaveItemData(index)
                    
        except Exception as e:
            self.dataValidationSignal.emit(f"Error updating image: {e}", True)
    
    @Slot(str, str, int)
    def copyImageToProject(self, source_path: str, file_name: str, index: int):
        """Copy an image file to the project images directory"""
        try:
            import shutil
            from pathlib import Path
            
            source = Path(source_path)
            if not source.exists():
                self.dataValidationSignal.emit(f"Source file not found: {source_path}", True)
                return
            
            # Ensure unique filename
            dest_path = self._processor.blog_images_dir / file_name
            counter = 1
            original_stem = dest_path.stem
            original_suffix = dest_path.suffix
            
            while dest_path.exists():
                dest_path = self._processor.blog_images_dir / f"{original_stem}_{counter}{original_suffix}"
                counter += 1
            
            # Copy the file
            shutil.copy2(source, dest_path)
            
            # Update the item with the new image
            final_filename = dest_path.name
            self.updateItemImage(index, final_filename)
            
            self.status = f"✅ Image copied and applied: {final_filename}"
            
        except Exception as e:
            self.dataValidationSignal.emit(f"Failed to copy image: {e}", True)
    
    def _autoSaveItemData(self, index: int):
        """Immediately save item data for published blogs"""
        try:
            item = self._blog_model.getItem(index)
            if not item or item.status != "published":
                return
            
            # Update the published blog with current data
            self.updatePublishedBlog(index)
            
        except Exception as e:
            self.dataValidationSignal.emit(f"Auto-save failed: {e}", True)
    
    def _scheduleAutoSave(self, index: int):
        """Schedule debounced auto-save for content changes"""
        # Cancel existing timer for this item
        if index in self._auto_save_timers:
            timer = self._auto_save_timers[index]
            if timer and timer.isActive():
                timer.stop()
        
        # Create new timer
        from PySide6.QtCore import QTimer
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._autoSaveItemData(index))
        timer.start(self._debounce_delay)
        
        self._auto_save_timers[index] = timer
    
    @Slot(result=bool)
    def hasUnsavedChanges(self):
        """Check if there are any unsaved changes"""
        for i in range(self._blog_model.rowCount()):
            item = self._blog_model.getItem(i)
            if item and item.status == "published":
                # Check if there are pending auto-save timers
                if i in self._auto_save_timers:
                    timer = self._auto_save_timers[i]
                    if timer and timer.isActive():
                        return True
        return False
    
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
    # Enable high DPI scaling
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
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