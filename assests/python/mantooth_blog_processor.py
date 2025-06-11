#!/usr/bin/env python3
"""
Mantooth Blog Processor - Interactive PDF processing
User selects individual PDFs to process with enhanced formatting and link detection
"""

import os
import sys
import json
import re
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed. Run: pip install pdfplumber")
    sys.exit(1)

class MantoothBlogProcessor:
    def __init__(self):
        # Auto-detect project root
        self.project_root = self.find_project_root()
        
        if not self.project_root:
            print("ERROR: Could not find project root. Please run from the main project directory.")
            sys.exit(1)
        
        print(f"✅ Project root found: {self.project_root}")
        
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

    def find_project_root(self) -> Optional[Path]:
        """Find project root by looking for key files"""
        current_path = Path.cwd()
        script_path = Path(__file__).parent
        
        # Look upward from current directory
        search_paths = [current_path]
        temp_path = current_path
        for _ in range(5):  # Look up to 5 levels up
            temp_path = temp_path.parent
            search_paths.append(temp_path)
        
        # Also check relative to script location
        search_paths.extend([
            script_path.parent,
            script_path.parent.parent,
        ])
        
        for root in search_paths:
            # Look for key files that indicate project root
            if (root / "blogs.html").exists() and (root / "assests").exists():
                return root
            # Fallback: just look for assests folder
            elif (root / "assests" / "Blogs").exists() and (root / "index.html").exists():
                return root
        
        return None

    def load_configuration(self) -> Dict:
        """Load processing configuration"""
        default_config = {
            "autoTags": True,
            "autoExcerpts": True,
            "updateBlogsPage": True,
            "maxExcerptLength": 200,
            "maxTagsPerPost": 6,
            "preserveFormatting": True,
            "detectLinks": True
        }
        
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return {**default_config, **config}
            else:
                return default_config
        except Exception:
            return default_config

    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def list_available_pdfs(self) -> List[Path]:
        """List all available PDF files"""
        if not self.raw_blogs_dir.exists():
            return []
        return list(self.raw_blogs_dir.glob("*.pdf"))

    def select_pdf_interactive(self) -> Optional[Path]:
        """Interactive PDF selection"""
        pdfs = self.list_available_pdfs()
        
        if not pdfs:
            print(f"\n❌ No PDF files found in {self.raw_blogs_dir}")
            print(f"💡 Please add PDF files to process")
            return None
        
        print(f"\n📂 Found {len(pdfs)} PDF files:")
        print("=" * 50)
        
        for i, pdf in enumerate(pdfs, 1):
            # Get file info
            size_mb = pdf.stat().st_size / (1024 * 1024)
            modified = datetime.fromtimestamp(pdf.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            
            print(f"{i:2d}. {pdf.name}")
            print(f"    📊 Size: {size_mb:.1f} MB | Modified: {modified}")
        
        print("=" * 50)
        
        while True:
            try:
                choice = input(f"\nSelect a PDF to process (1-{len(pdfs)}) or 'q' to quit: ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(pdfs):
                    selected = pdfs[index]
                    print(f"\n✅ Selected: {selected.name}")
                    return selected
                else:
                    print(f"❌ Please enter a number between 1 and {len(pdfs)}")
            
            except ValueError:
                print("❌ Please enter a valid number or 'q' to quit")
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                return None

    def extract_text_from_pdf(self, pdf_path: Path) -> Optional[Dict]:
        """Extract text and metadata from PDF"""
        self.log(f"📄 Extracting text from: {pdf_path.name}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                pages_data = []
                links = []
                
                for page_num, page in enumerate(pdf.pages, 1):
                    self.log(f"   Processing page {page_num}/{len(pdf.pages)}")
                    
                    # Extract text
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n\n"
                        pages_data.append({
                            'page': page_num,
                            'text': text.strip(),
                            'char_count': len(text)
                        })
                    
                    # Extract links/annotations
                    if self.config.get('detectLinks', True):
                        page_links = self.extract_links_from_page(page)
                        links.extend(page_links)
                
                if not full_text.strip():
                    raise ValueError("No text content found")
                
                result = {
                    'text': full_text.strip(),
                    'pages': pages_data,
                    'links': links,
                    'total_pages': len(pdf.pages),
                    'total_chars': len(full_text)
                }
                
                self.log(f"✅ Extracted {len(full_text)} characters, {len(links)} links")
                return result
                
        except Exception as e:
            self.log(f"❌ Error extracting from {pdf_path.name}: {e}", "ERROR")
            return None

    def extract_links_from_page(self, page) -> List[Dict]:
        """Extract links from a PDF page"""
        links = []
        
        try:
            # Get annotations (links)
            if hasattr(page, 'annots') and page.annots:
                for annot in page.annots:
                    if annot.get('subtype') == 'Link':
                        uri = annot.get('uri')
                        if uri:
                            links.append({
                                'url': uri,
                                'type': 'annotation',
                                'page': page.page_number
                            })
            
            # Also look for URL patterns in text
            text = page.extract_text()
            if text:
                url_patterns = [
                    r'https?://[^\s\)]+',
                    r'www\.[^\s\)]+',
                    r'[a-zA-Z0-9.-]+\.(com|org|net|edu|gov|io|co)[^\s\)]*'
                ]
                
                for pattern in url_patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        url = match.group().rstrip('.,;!?')
                        if not url.startswith('http'):
                            url = 'https://' + url
                        
                        links.append({
                            'url': url,
                            'type': 'text_pattern',
                            'page': page.page_number,
                            'context': text[max(0, match.start()-20):match.end()+20]
                        })
        
        except Exception as e:
            self.log(f"Warning: Could not extract links from page: {e}", "WARN")
        
        return links

    def clean_and_format_text(self, raw_text: str, links: List[Dict]) -> str:
        """Enhanced text cleaning and formatting"""
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', raw_text)
        
        # Better paragraph detection
        # Split on sentence endings followed by capital letters
        cleaned = re.sub(r'([.!?])\s*([A-Z][a-z])', r'\1\n\n\2', cleaned)
        
        # Handle common PDF artifacts
        cleaned = re.sub(r'Page \d+', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\f', '\n\n', cleaned)
        cleaned = re.sub(r'^\d+\s*$', '', cleaned, flags=re.MULTILINE)  # Remove standalone numbers
        
        # Fix common formatting issues
        cleaned = re.sub(r'\s*\n\s*\n\s*', '\n\n', cleaned)  # Normalize paragraph breaks
        cleaned = re.sub(r'([a-z])([A-Z])', r'\1. \2', cleaned)  # Add periods between sentences
        
        # Handle bullet points and lists
        cleaned = re.sub(r'\n(\s*)[•·▪▫‣⁃]\s*', r'\n\1• ', cleaned)
        cleaned = re.sub(r'\n(\s*)[-*]\s*', r'\n\1• ', cleaned)
        
        # Convert URLs to markdown-style links if found
        if self.config.get('detectLinks', True) and links:
            cleaned = self.convert_links_to_markdown(cleaned, links)
        
        return cleaned.strip()

    def convert_links_to_markdown(self, text: str, links: List[Dict]) -> str:
        """Convert detected URLs to markdown-style links"""
        for link in links:
            url = link['url']
            # Create a simple markdown link
            if url in text:
                # Try to find context for a better link text
                link_text = self.get_link_context(url, text)
                markdown_link = f"[{link_text}]({url})"
                text = text.replace(url, markdown_link)
        
        return text

    def get_link_context(self, url: str, text: str) -> str:
        """Get meaningful context for a link"""
        # Find the URL in text and get surrounding context
        url_pos = text.find(url)
        if url_pos == -1:
            return url
        
        # Look for meaningful text before the URL
        start = max(0, url_pos - 50)
        before_text = text[start:url_pos].strip()
        
        # Extract last few words that might be descriptive
        words = before_text.split()
        if len(words) >= 2:
            return ' '.join(words[-2:])
        elif len(words) == 1:
            return words[-1]
        else:
            # Fallback to domain name
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                return domain.replace('www.', '')
            except:
                return url

    def format_content_to_html(self, content: str) -> str:
        """Convert text to well-formatted HTML"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        html_paragraphs = []
        
        for para in paragraphs:
            # Handle lists
            if '• ' in para:
                list_items = para.split('• ')
                if len(list_items) > 1:
                    # Create an unordered list
                    html_para = "                    <ul>\n"
                    for item in list_items[1:]:  # Skip first empty item
                        if item.strip():
                            html_para += f"                        <li>{item.strip()}</li>\n"
                    html_para += "                    </ul>"
                    html_paragraphs.append(html_para)
                    continue
            
            # Handle markdown-style links
            para = self.convert_markdown_links_to_html(para)
            
            # Regular paragraph
            html_paragraphs.append(f"                    <p>{para}</p>")
        
        return '\n\n'.join(html_paragraphs)

    def convert_markdown_links_to_html(self, text: str) -> str:
        """Convert markdown-style links to HTML"""
        # Pattern for [text](url)
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        
        def replace_link(match):
            link_text = match.group(1)
            url = match.group(2)
            return f'<a href="{url}" target="_blank">{link_text}</a>'
        
        return re.sub(link_pattern, replace_link, text)

    def preview_blog_content(self, blog_data: Dict) -> bool:
        """Show a preview and ask for confirmation"""
        print("\n" + "="*60)
        print("📋 BLOG PREVIEW")
        print("="*60)
        print(f"Title: {blog_data['title']}")
        print(f"Slug: {blog_data['slug']}")
        print(f"Tags: {', '.join(blog_data['tags'])}")
        print(f"Image: {blog_data['featured_image']}")
        print(f"Publish Date: {blog_data['formatted_date']}")
        print()
        print("Excerpt:")
        print("-" * 40)
        print(blog_data['excerpt'])
        print()
        
        # Show first few paragraphs of content
        content_preview = blog_data['content'][:500]
        if len(blog_data['content']) > 500:
            content_preview += "..."
        
        print("Content Preview:")
        print("-" * 40)
        # Remove HTML tags for preview
        clean_preview = re.sub(r'<[^>]+>', '', content_preview)
        print(clean_preview)
        print("="*60)
        
        while True:
            choice = input("\nGenerate this blog? (y/n/e to edit): ").strip().lower()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            elif choice in ['e', 'edit']:
                self.edit_blog_data(blog_data)
                return True
            else:
                print("Please enter 'y' for yes, 'n' for no, or 'e' to edit")

    def edit_blog_data(self, blog_data: Dict):
        """Allow user to edit blog data before generation"""
        print("\n📝 Edit Blog Data:")
        print("(Press Enter to keep current value)")
        
        # Edit title
        new_title = input(f"Title [{blog_data['title']}]: ").strip()
        if new_title:
            blog_data['title'] = new_title
            blog_data['slug'] = self.generate_slug(new_title)
        
        # Edit tags
        current_tags = ', '.join(blog_data['tags'])
        new_tags = input(f"Tags [{current_tags}]: ").strip()
        if new_tags:
            blog_data['tags'] = [tag.strip() for tag in new_tags.split(',')]
        
        # Edit excerpt
        print(f"\nCurrent excerpt:\n{blog_data['excerpt']}")
        new_excerpt = input("New excerpt (or press Enter to keep): ").strip()
        if new_excerpt:
            blog_data['excerpt'] = new_excerpt

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

    def generate_excerpt(self, content: str) -> str:
        """Generate excerpt from content"""
        if not self.config.get('autoExcerpts', True):
            return "No excerpt generated."
        
        max_length = self.config.get('maxExcerptLength', 200)
        
        # Remove HTML tags for excerpt
        clean_content = re.sub(r'<[^>]+>', '', content)
        paragraphs = [p.strip() for p in clean_content.split('\n\n') if len(p.strip()) > 50]
        
        if paragraphs:
            first_para = paragraphs[0]
            if len(first_para) <= max_length:
                return first_para
            else:
                excerpt = first_para[:max_length]
                last_space = excerpt.rfind(' ')
                if last_space > max_length * 0.8:
                    excerpt = excerpt[:last_space]
                return excerpt + "..."
        
        return clean_content[:max_length] + "..." if len(clean_content) > max_length else clean_content

    def suggest_tags(self, title: str, content: str) -> List[str]:
        """Suggest tags based on content analysis"""
        if not self.config.get('autoTags', True):
            return ['lifestyle']
        
        content_lower = (title + " " + content).lower()
        suggested_tags = []
        
        # Location tags
        location_keywords = {
            'phoenix': ['phoenix', 'arizona', 'az'],
            'arizona': ['arizona', 'az', 'desert'],
            'gatlinburg': ['gatlinburg', 'tennessee', 'tn'],
            'los angeles': ['los angeles', 'la', 'california'],
            'renaissance festival': ['renaissance', 'ren fest', 'festival', 'medieval']
        }
        
        for tag, keywords in location_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                suggested_tags.append(tag)
        
        # Activity tags
        activity_keywords = {
            'food': ['restaurant', 'food', 'eat', 'dining', 'meal'],
            'restaurants': ['restaurant', 'dining', 'eatery', 'bistro'],
            'cocktails': ['cocktail', 'drink', 'bar', 'alcohol'],
            'music': ['music', 'concert', 'band', 'performance'],
            'concerts': ['concert', 'live music', 'performance', 'venue'],
            'travel': ['travel', 'trip', 'vacation', 'journey'],
            'hiking': ['hike', 'hiking', 'trail', 'mountain'],
            'events': ['festival', 'event', 'celebration'],
            'pets': ['cat', 'pet', 'animal'],
            'cats': ['cat', 'feline', 'kitty'],
            'reviews': ['review', 'opinion', 'experience']
        }
        
        for tag, keywords in activity_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                suggested_tags.append(tag)
        
        suggested_tags.append('lifestyle')
        
        max_tags = self.config.get('maxTagsPerPost', 6)
        return list(dict.fromkeys(suggested_tags))[:max_tags]

    def generate_image_name(self, pdf_filename: str) -> str:
        """Generate image filename"""
        base_name = pdf_filename.replace('.pdf', '').lower()
        base_name = re.sub(r'[^a-z0-9]', '_', base_name)
        base_name = re.sub(r'_+', '_', base_name).strip('_')
        return f"{base_name}_blog.png"

    def create_blog_html(self, blog_data: Dict) -> str:
        """Generate blog HTML file"""
        template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Mantooth</title>
    <link rel="stylesheet" href="../CSS/style.css">
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
                
                <img src="../Images/{featured_image}" alt="{title}" class="blog-featured-image">
                
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
                <a href="#">Twitter</a>
                <a href="#">Facebook</a>
                <a href="#">Instagram</a>
            </div>
        </div>
    </footer>
    
    <script src="../JS/clickable-cards.js"></script>
</body>
</html>'''
        
        tags_html = '\n'.join([f'                    <span class="tag">{tag.title()}</span>' for tag in blog_data['tags']])
        
        return template.format(
            title=blog_data['title'],
            formatted_date=blog_data['formatted_date'],
            featured_image=blog_data['featured_image'],
            content=blog_data['content'],
            tags_html=tags_html
        )

    def update_blogs_html(self, blog_data: Dict) -> bool:
        """Update blogs.html with new entry"""
        if not self.config.get('updateBlogsPage', True):
            self.log("Skipping blogs.html update (disabled in config)")
            return True
            
        self.log("📝 Updating blogs.html")
        
        if not self.blogs_html_path.exists():
            self.log(f"❌ blogs.html not found at {self.blogs_html_path}", "ERROR")
            return False
        
        try:
            with open(self.blogs_html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find blogs-grid section
            grid_start = content.find('<section class="blogs-grid">')
            grid_end = content.find('</section>', grid_start)
            
            if grid_start == -1 or grid_end == -1:
                self.log("❌ Could not find blogs-grid section", "ERROR")
                return False
            
            # Generate new blog item
            item_html = f'''                <!-- Blog Post - {blog_data['title']} -->
                <article class="blog-item clickable-card" data-tags="{','.join(blog_data['tags'])}" data-url="assests/Blogs/{blog_data['slug']}.html">
                    <img src="assests/Images/{blog_data['featured_image']}" alt="{blog_data['title']}">
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
            
            # Insert new item at beginning of grid
            existing_section = content[grid_start:grid_end + 10]
            insertion_point = existing_section.find('>', existing_section.find('<section class="blogs-grid">')) + 1
            
            updated_section = (existing_section[:insertion_point] + 
                              '\n' + item_html + '\n                \n' + 
                              existing_section[insertion_point:])
            
            # Replace in full content
            updated_html = content[:grid_start] + updated_section + content[grid_end + 10:]
            
            with open(self.blogs_html_path, 'w', encoding='utf-8') as f:
                f.write(updated_html)
            
            self.log("✅ blogs.html updated successfully")
            return True
            
        except Exception as e:
            self.log(f"❌ Error updating blogs.html: {e}", "ERROR")
            return False

    def process_single_pdf(self, pdf_path: Path) -> bool:
        """Process a single PDF file"""
        self.log(f"🔄 Processing {pdf_path.name}")
        
        # Extract text and metadata
        extraction_result = self.extract_text_from_pdf(pdf_path)
        if not extraction_result:
            return False
        
        # Process the extracted data
        cleaned_text = self.clean_and_format_text(extraction_result['text'], extraction_result['links'])
        title = self.extract_title_from_filename(pdf_path.name)
        slug = self.generate_slug(title)
        tags = self.suggest_tags(title, cleaned_text)
        content_html = self.format_content_to_html(cleaned_text)
        excerpt = self.generate_excerpt(content_html)
        featured_image = self.generate_image_name(pdf_path.name)
        
        # Prepare blog data
        blog_data = {
            'title': title,
            'slug': slug,
            'content': content_html,
            'excerpt': excerpt,
            'tags': tags,
            'featured_image': featured_image,
            'publish_date': datetime.now().strftime("%Y-%m-%d"),
            'formatted_date': datetime.now().strftime("%B %d, %Y"),
            'links_found': len(extraction_result['links']),
            'source_file': pdf_path.name
        }
        
        # Show preview and get confirmation
        if not self.preview_blog_content(blog_data):
            print("❌ Blog generation cancelled")
            return False
        
        # Generate and save HTML file
        blog_html = self.create_blog_html(blog_data)
        blog_file_path = self.blogs_dir / f"{slug}.html"
        
        try:
            with open(blog_file_path, 'w', encoding='utf-8') as f:
                f.write(blog_html)
            
            self.log(f"✅ Created: {blog_file_path}")
            
            # Check if image exists
            image_path = self.images_dir / featured_image
            if not image_path.exists():
                self.log(f"⚠️  Image needed: {featured_image}")
                print(f"💡 Add image to: {self.images_dir / featured_image}")
            
            # Update blogs.html
            self.update_blogs_html(blog_data)
            
            # Update JSON data
            self.update_blog_data_json([blog_data])
            
            print(f"\n🎉 Blog generated successfully!")
            print(f"📄 File: {blog_file_path}")
            print(f"🖼️  Image needed: {featured_image}")
            print(f"🏷️  Tags: {', '.join(tags)}")
            if extraction_result['links']:
                print(f"🔗 Links found: {len(extraction_result['links'])}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error creating blog: {e}", "ERROR")
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
                    "source": "PDF Processing",
                    "sourceFile": blog.get('source_file', ''),
                    "linksFound": blog.get('links_found', 0)
                }
                data["posts"].insert(0, post_data)
            
            data["lastUpdated"] = datetime.now().isoformat()
            data["totalPosts"] = len(data["posts"])
            
            with open(self.blog_data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
        except Exception as e:
            self.log(f"❌ Error saving blog data: {e}", "ERROR")

    def calculate_read_time(self, content: str) -> int:
        """Calculate estimated reading time"""
        text = re.sub(r'<[^>]+>', '', content)
        words = len(text.split())
        return max(1, round(words / 200))

    def run_interactive(self):
        """Main interactive processing loop"""
        print("🦷 Mantooth Blog Processor - Interactive Mode")
        print("=" * 50)
        
        while True:
            pdf_path = self.select_pdf_interactive()
            
            if pdf_path is None:
                print("\n👋 Goodbye!")
                break
            
            success = self.process_single_pdf(pdf_path)
            
            if success:
                # Ask if user wants to process another
                while True:
                    continue_choice = input("\nProcess another PDF? (y/n): ").strip().lower()
                    if continue_choice in ['y', 'yes']:
                        break
                    elif continue_choice in ['n', 'no']:
                        print("\n👋 All done!")
                        return
                    else:
                        print("Please enter 'y' for yes or 'n' for no")
            else:
                print("\n❌ Processing failed. Try another PDF?")

def main():
    """Main entry point"""
    try:
        processor = MantoothBlogProcessor()
        processor.run_interactive()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
