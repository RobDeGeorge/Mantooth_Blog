#!/usr/bin/env python3
"""
Mantooth Blog Processor - Balanced Paragraph Detection
Converts PDF files to formatted HTML blog posts
"""

import os
import sys
import json
import re
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
        self.raw_blogs_dir = self.project_root / "website" / "blog-processor" / "input"
        self.blogs_dir = self.project_root / "website" / "blog-processor" / "output"
        self.blog_images_dir = self.project_root / "website" / "blog-processor" / "images"
        self.website_images_dir = self.project_root / "website" / "assets" / "images"
        self.json_dir = self.project_root / "website" / "assets" / "data"
        
        self.blogs_html_path = self.project_root / "website" / "blogs.html"
        self.config_path = self.json_dir / "processing-config.json"
        self.blog_data_path = self.json_dir / "blog-data.json"
        
        # Create directories if needed
        self.blogs_dir.mkdir(parents=True, exist_ok=True)
        self.blog_images_dir.mkdir(parents=True, exist_ok=True)
        self.json_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self.load_configuration()
        
        print(f"📁 Raw Blogs directory: {self.raw_blogs_dir}")
        print(f"📁 Output directory: {self.blogs_dir}")

    def find_project_root(self) -> Optional[Path]:
        """Find project root by looking for key files"""
        current_path = Path.cwd()
        script_path = Path(__file__).parent
        
        search_paths = [current_path]
        temp_path = current_path
        for _ in range(5):
            temp_path = temp_path.parent
            search_paths.append(temp_path)
        
        search_paths.extend([
            script_path.parent,
            script_path.parent.parent,
        ])
        
        for root in search_paths:
            if (root / "website" / "blogs.html").exists() and (root / "website" / "assets").exists():
                return root
            elif (root / "website" / "index.html").exists() and (root / "website" / "blog-processor").exists():
                return root
            elif (root / "blogs.html").exists() and (root / "assests").exists():
                return root  # Fallback for old structure
        
        return None

    def load_configuration(self) -> Dict:
        """Load processing configuration"""
        default_config = {
            "autoExcerpts": True,
            "updateBlogsPage": True,
            "maxExcerptLength": 200,
            "minParagraphLength": 50
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
        """Extract text from PDF - balanced approach"""
        self.log(f"📄 Extracting text from: {pdf_path.name}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                
                for page_num, page in enumerate(pdf.pages, 1):
                    self.log(f"   Processing page {page_num}/{len(pdf.pages)}")
                    
                    # Extract text WITHOUT layout preservation (cleaner for our needs)
                    text = page.extract_text()
                    
                    if text:
                        # Add page separator
                        if page_num > 1:
                            full_text += ""
                        full_text += text
                
                if not full_text.strip():
                    raise ValueError("No text content found")
                
                # Now detect paragraphs from the full text
                paragraphs = self.detect_paragraphs(full_text)
                
                result = {
                    'paragraphs': paragraphs,
                    'text': '\n\n'.join(paragraphs),
                    'total_pages': len(pdf.pages),
                    'total_paragraphs': len(paragraphs)
                }
                
                self.log(f"✅ Extracted {len(paragraphs)} paragraphs from {len(pdf.pages)} pages")
                return result
                
        except Exception as e:
            self.log(f"❌ Error extracting from {pdf_path.name}: {e}", "ERROR")
            return None

    def detect_paragraphs(self, text: str) -> List[str]:
        """
        Robust paragraph detection that survives PDFs where leading spaces
        are stripped out.
    
        Rules, in order of preference:
        1. A truly blank line       → paragraph break.
        2. A line indented ≥ 2 spc  → paragraph break (if we already have content).
        3. Sentence-boundary check  → previous line ends with .?! and this line
           starts with an uppercase letter (and we already have content).
        """
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    
        paragraphs: List[str] = []
        current:  List[str] = []
    
        for line in lines:
            raw = line.rstrip()
            if not raw.strip():                         # rule-1
                if current:
                    paragraphs.append(self.clean_paragraph_text(" ".join(current)))
                    current = []
                continue
    
            indent = len(raw) - len(raw.lstrip())
            new_para = False
    
            if indent >= 2 and current:                 # rule-2
                new_para = True
            elif (current and
                  current[-1][-1] in ".?!" and          # rule-3
                  raw.lstrip()[:1].isupper()):
                new_para = True
    
            if new_para:
                paragraphs.append(self.clean_paragraph_text(" ".join(current)))
                current = [raw.strip()]
            else:
                current.append(raw.strip())
    
        if current:
            paragraphs.append(self.clean_paragraph_text(" ".join(current)))

        # Optional fix — remove duplicate title if it was embedded in the first paragraph
        if hasattr(self, 'selected_pdf') and self.selected_pdf:
            filename_title = self.extract_title_from_filename(self.selected_pdf.name).rstrip(":").lower()
            if paragraphs:
                first = paragraphs[0]
                if first.lower().startswith(filename_title):
                    trimmed = first[len(filename_title):].lstrip(": ").strip()
                    if trimmed:
                        paragraphs[0] = trimmed

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

    def format_content_to_html(self, paragraphs: List[str]) -> str:
        """
        Render HTML while ensuring the title (possibly spread over 1-3 very-short
        paragraphs) is shown **once** at the top and never duplicated in the body.

        Heuristic:
          • Peel off consecutive leading paragraphs that
              – are short (≤ 10 words) **and**
              – do NOT end with a sentence terminator (. ! ?)

            These lines are treated as the *title block*.
          • Everything that follows is treated as normal body content.
        """

        if not paragraphs:
            return ""

        # --- 1. Collect the title block -----------------------------------------
        title_parts = []
        while paragraphs:
            cand = paragraphs[0].strip()
            word_cnt = len(cand.split())

            if word_cnt > 10 or cand[-1] in ".!?":
                break                           # reached the real body – stop peeling

            # pop from list & add to title_parts
            title_parts.append(paragraphs.pop(0).rstrip(":").strip())

            # safeguard: don’t peel more than 3 little lines
            if len(title_parts) == 3:
                break

        # fallback: if we accidentally peeled nothing, fall back to filename title
        if not title_parts:
            if hasattr(self, 'selected_pdf') and self.selected_pdf:
                title_parts.append(
                    self.extract_title_from_filename(self.selected_pdf.name)
                )
            else:
                title_parts.append("Blog Post")

        # Deduplicate exact repeats (e.g. “AZ Renaissance Festival” appears twice)
        seen = set()
        unique_parts = []
        for p in title_parts:
            key = p.lower()
            if key not in seen:
                unique_parts.append(p)
                seen.add(key)

        full_title = " – ".join(unique_parts)   # nice divider for multi-line titles

        # --- 2. Build the HTML ---------------------------------------------------
        html_elements: List[str] = []
        html_elements.append(
            f"                    <h3>{self.escape_html(full_title)}</h3>"
        )

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            # keep your existing rule: very-short line ending with ':'  → sub-header
            if para.endswith(':') and len(para) < 30:
                html_elements.append(
                    f"                    <h3>{self.escape_html(para.rstrip(':'))}</h3>"
                )
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

    def generate_excerpt(self, paragraphs: List[str]) -> str:
        """Generate excerpt from paragraphs"""
        if not self.config.get('autoExcerpts', True):
            return "No excerpt generated."
        
        max_length = self.config.get('maxExcerptLength', 200)
        
        # Use first non-header paragraph
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

    def get_tags_from_user(self, title: str) -> List[str]:
        """Get tags from user input"""
        print("\n🏷️  TAG SELECTION")
        print("-" * 40)
        print(f"Blog Title: {title}")
        print("\nPlease enter tags for this blog post.")
        print("Separate multiple tags with commas (e.g., phoenix, food, restaurants)")
        print("\nSuggested tag categories:")
        print("- Locations: phoenix, arizona, gatlinburg, los angeles, nashville")
        print("- Activities: food, restaurants, cocktails, music, concerts, travel, hiking")
        print("- General: lifestyle, events, reviews, pets, cats")
        print("-" * 40)
        
        while True:
            tags_input = input("\nEnter tags: ").strip()
            
            if not tags_input:
                print("❌ Please enter at least one tag.")
                continue
            
            tags = [tag.strip().lower() for tag in tags_input.split(',')]
            tags = [tag for tag in tags if tag]
            
            if not tags:
                print("❌ No valid tags entered. Please try again.")
                continue
            
            print(f"\n✅ Tags selected: {', '.join(tags)}")
            
            confirm = input("Are these tags correct? (y/n): ").strip().lower()
            
            if confirm in ['y', 'yes']:
                return tags
            elif confirm in ['n', 'no']:
                print("Let's try again...")

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

    def select_image_interactive(self, title: str) -> str:
        """Interactive image selection from available images"""
        available_images = self.list_available_images()
        
        if not available_images:
            print(f"\n⚠️  No images found in {self.blog_images_dir}")
            print("💡 Please add images to the blog-processor/images/ folder")
            default_name = f"{title.lower().replace(' ', '_')}_blog.png"
            print(f"💡 Will use placeholder: {default_name}")
            return default_name
        
        print(f"\n🖼️  IMAGE SELECTION")
        print("-" * 50)
        print(f"Blog Title: {title}")
        print(f"\nFound {len(available_images)} images in {self.blog_images_dir.name}/:")
        print("=" * 40)
        
        for i, image in enumerate(available_images, 1):
            image_path = self.blog_images_dir / image
            size_kb = image_path.stat().st_size / 1024
            modified = datetime.fromtimestamp(image_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            
            print(f"{i:2d}. {image}")
            print(f"    📊 Size: {size_kb:.1f} KB | Modified: {modified}")
        
        print("=" * 40)
        
        while True:
            try:
                choice = input(f"\nSelect an image (1-{len(available_images)}): ").strip()
                
                index = int(choice) - 1
                if 0 <= index < len(available_images):
                    selected = available_images[index]
                    print(f"\n✅ Selected image: {selected}")
                    return selected
                else:
                    print(f"❌ Please enter a number between 1 and {len(available_images)}")
            
            except ValueError:
                print("❌ Please enter a valid number")
            except KeyboardInterrupt:
                print("\n\n👋 Using default placeholder image")
                default_name = f"{title.lower().replace(' ', '_')}_blog.png"
                return default_name

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
        print(f"Paragraphs: {blog_data['paragraph_count']}")
        print()
        print("Excerpt:")
        print("-" * 40)
        print(blog_data['excerpt'])
        print()
        
        # Show paragraph beginnings
        print("Paragraph beginnings:")
        print("-" * 40)
        for i, para in enumerate(blog_data['paragraphs']):
            print(f"\nParagraph {i+1}: {para[:80]}...")
        print("="*60)
        
        while True:
            choice = input("\nGenerate this blog? (y/n): ").strip().lower()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False

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
                <a href="#">Twitter</a>
                <a href="#">Facebook</a>
                <a href="#">Instagram</a>
            </div>
        </div>
    </footer>

    <script src="../../assets/js/clickable-cards.js"></script>
</body>
</html>'''
        
        tags_html = '\n'.join([f'                    <span class="tag">{tag.title()}</span>' for tag in blog_data['tags']])
        
        # Generate image HTML only if there's an image
        featured_image = blog_data.get('featured_image', '')
        if featured_image and featured_image.strip():
            featured_image_html = f'                <img src="../images/{featured_image}" alt="{blog_data["title"]}" class="blog-featured-image">'
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
            
            grid_start = content.find('<section class="blogs-grid">')
            grid_end = content.find('</section>', grid_start)
            
            if grid_start == -1 or grid_end == -1:
                self.log("❌ Could not find blogs-grid section", "ERROR")
                return False
            
            item_html = f'''                <!-- Blog Post - {blog_data['title']} -->
                <article class="blog-item clickable-card" data-tags="{','.join(blog_data['tags'])}" data-url="blog-processor/output/{blog_data['slug']}.html">
                    <img src="blog-processor/images/{blog_data['featured_image']}" alt="{blog_data['title']}">
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
            
            self.log("✅ blogs.html updated successfully")
            return True
            
        except Exception as e:
            self.log(f"❌ Error updating blogs.html: {e}", "ERROR")
            return False

    def is_pdf_already_processed(self, pdf_path: Path) -> bool:
        """Check if PDF has already been processed"""
        title = self.extract_title_from_filename(pdf_path.name)
        slug = self.generate_slug(title)
        
        # Check if blog data exists
        if self.blog_data_path.exists():
            try:
                with open(self.blog_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                existing_slugs = {post.get("slug", "") for post in data.get("posts", [])}
                return slug in existing_slugs
            except Exception:
                return False
        return False
    
    def process_single_pdf(self, pdf_path: Path, force_overwrite: bool = False) -> bool:
        """Process a single PDF file"""
        self.selected_pdf = pdf_path
        
        # Check if already processed
        if not force_overwrite and self.is_pdf_already_processed(pdf_path):
            self.log(f"⚠️  {pdf_path.name} already processed - skipping")
            return True
        
        self.log(f"🔄 Processing {pdf_path.name}")
        
        # Extract text
        extraction_result = self.extract_text_from_pdf(pdf_path)
        if not extraction_result:
            return False
        
        paragraphs = extraction_result['paragraphs']
        
        # Extract title and generate initial data
        title = self.extract_title_from_filename(pdf_path.name)
        slug = self.generate_slug(title)
        content_html = self.format_content_to_html(paragraphs)
        excerpt = self.generate_excerpt(paragraphs)
        
        # Get tags from user
        tags = self.get_tags_from_user(title)
        
        # Get image selection from user
        featured_image = self.select_image_interactive(title)
        
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
            'source_file': pdf_path.name,
            'paragraphs': paragraphs,
            'paragraph_count': len(paragraphs)
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
            image_path = self.blog_images_dir / featured_image
            if not image_path.exists():
                self.log(f"⚠️  Image needed: {featured_image}")
                print(f"💡 Add image to: {self.blog_images_dir / featured_image}")
            
            # Update blogs.html
            self.update_blogs_html(blog_data)
            
            # Update JSON data
            self.update_blog_data_json([blog_data])
            
            print(f"\n🎉 Blog generated successfully!")
            print(f"📄 File: {blog_file_path}")
            print(f"🖼️  Image needed: {featured_image}")
            print(f"🏷️  Tags: {', '.join(tags)}")
            print(f"📊 Paragraphs detected: {len(paragraphs)}")
            
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
                    "paragraphCount": blog.get('paragraph_count', 0)
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
    
    def process_all_pdfs(self):
        """Process all PDFs in the Raw Blogs folder"""
        print("🦷 Mantooth Blog Processor - Batch Mode")
        print("=" * 50)
        
        pdfs = self.list_available_pdfs()
        
        if not pdfs:
            print(f"\n❌ No PDF files found in {self.raw_blogs_dir}")
            print(f"💡 Please add PDF files to process")
            return
        
        print(f"\n📂 Found {len(pdfs)} PDF files to process:")
        for i, pdf in enumerate(pdfs, 1):
            size_mb = pdf.stat().st_size / (1024 * 1024)
            print(f"  {i}. {pdf.name} ({size_mb:.1f} MB)")
        
        print("\n" + "="*50)
        proceed = input(f"Process all {len(pdfs)} PDFs? (y/n): ").strip().lower()
        if proceed not in ['y', 'yes']:
            print("❌ Processing cancelled")
            return
        
        print("\n🚀 Starting batch processing...\n")
        
        success_count = 0
        failed_count = 0
        
        for i, pdf_path in enumerate(pdfs, 1):
            print(f"\n📄 Processing {i}/{len(pdfs)}: {pdf_path.name}")
            print("-" * 40)
            
            try:
                success = self.process_single_pdf(pdf_path)
                if success:
                    success_count += 1
                    print(f"✅ Successfully processed: {pdf_path.name}")
                else:
                    failed_count += 1
                    print(f"❌ Failed to process: {pdf_path.name}")
                    
            except Exception as e:
                failed_count += 1
                self.log(f"❌ Error processing {pdf_path.name}: {e}", "ERROR")
                
            # Small delay between processing
            if i < len(pdfs):
                print("\n" + "⏳ Moving to next PDF...")
        
        print("\n" + "="*60)
        print("📊 BATCH PROCESSING COMPLETE")
        print("="*60)
        print(f"✅ Successfully processed: {success_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📈 Total: {len(pdfs)}")
        
        if success_count > 0:
            print(f"\n🎉 Generated {success_count} new blog posts!")
            print(f"📁 Check your website's blog section")
    
    def run_interactive(self):
        """Main processing loop with mode selection"""
        print("🦷 Mantooth Blog Processor - Balanced Paragraph Detection")
        print("=" * 50)
        
        pdfs = self.list_available_pdfs()
        if not pdfs:
            print(f"\n❌ No PDF files found in {self.raw_blogs_dir}")
            print(f"💡 Please add PDF files to process")
            return
        
        print(f"\n📂 Found {len(pdfs)} PDF files")
        print("\nChoose processing mode:")
        print("1. Process all PDFs (Recommended)")
        print("2. Select individual PDFs")
        print("3. Edit existing blog images")
        
        while True:
            choice = input("\nSelect mode (1, 2, or 3): ").strip()
            if choice == "1":
                self.process_all_pdfs()
                break
            elif choice == "2":
                self.run_single_mode()
                break
            elif choice == "3":
                self.edit_blog_images()
                break
            else:
                print("❌ Please enter 1, 2, or 3")
    
    def edit_blog_images(self):
        """Edit images for existing blog posts"""
        print("\n🖼️  EDIT BLOG IMAGES")
        print("=" * 50)
        
        # Load existing blog data
        if not self.blog_data_path.exists():
            print("❌ No blog data found. Please process some PDFs first.")
            return
        
        try:
            with open(self.blog_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ Error loading blog data: {e}")
            return
        
        posts = data.get("posts", [])
        if not posts:
            print("❌ No blog posts found.")
            return
        
        print(f"\nFound {len(posts)} blog posts:")
        print("-" * 40)
        
        for i, post in enumerate(posts, 1):
            print(f"{i:2d}. {post['title']}")
            print(f"    Current image: {post['featuredImage']}")
            print(f"    Published: {post['publishDate']}")
        
        print("-" * 40)
        
        while True:
            try:
                choice = input(f"\nSelect a blog to edit image (1-{len(posts)}) or 'q' to quit: ").strip()
                
                if choice.lower() == 'q':
                    return
                
                index = int(choice) - 1
                if 0 <= index < len(posts):
                    selected_post = posts[index]
                    break
                else:
                    print(f"❌ Please enter a number between 1 and {len(posts)}")
            
            except ValueError:
                print("❌ Please enter a valid number or 'q' to quit")
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                return
        
        # Select new image
        new_image = self.select_image_interactive(selected_post['title'])
        
        # Update the post data
        old_image = selected_post['featuredImage']
        selected_post['featuredImage'] = new_image
        data['lastUpdated'] = datetime.now().isoformat()
        
        # Save updated data
        try:
            with open(self.blog_data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            # Update the blogs.html file
            self.update_blogs_html_image(selected_post['slug'], old_image, new_image)
            
            # Update the individual blog HTML file
            self.update_blog_post_image(selected_post['slug'], new_image)
            
            print(f"\n✅ Updated '{selected_post['title']}' image from '{old_image}' to '{new_image}'")
            print(f"📄 Updated blog data, blogs.html, and individual blog post")
            
        except Exception as e:
            print(f"❌ Error saving changes: {e}")

    def update_blogs_html_image(self, slug: str, old_image: str, new_image: str):
        """Update image reference in blogs.html"""
        try:
            with open(self.blogs_html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for the specific blog article containing this slug
            slug_pattern = f'data-url="blog-processor/output/{slug}.html"'
            
            if slug_pattern in content:
                # Find the article block and update the image within it
                article_start = content.find(slug_pattern)
                if article_start != -1:
                    # Find the start of this article
                    article_start = content.rfind('<article', 0, article_start)
                    # Find the end of this article
                    article_end = content.find('</article>', article_start) + len('</article>')
                    
                    if article_start != -1 and article_end != -1:
                        article_content = content[article_start:article_end]
                        
                        # Handle different image update scenarios
                        if new_image and new_image.strip():
                            new_src = f'src="blog-processor/images/{new_image}"'
                            if old_image and old_image.strip():
                                # Replace existing image
                                old_src = f'src="blog-processor/images/{old_image}"'
                                updated_article = article_content.replace(old_src, new_src)
                            else:
                                # No old image, need to add img tag to existing structure
                                # This is complex for blogs.html, so just rebuild it
                                print("⚠️  Complex image update needed - please refresh the page")
                                updated_article = article_content
                        else:
                            # Remove image (set to empty)
                            if old_image and old_image.strip():
                                old_src = f'src="blog-processor/images/{old_image}"'
                                # This is also complex, just note it
                                print("⚠️  Image removal - please refresh the page")
                                updated_article = article_content
                            else:
                                updated_article = article_content
                        
                        content = content[:article_start] + updated_article + content[article_end:]
            
            with open(self.blogs_html_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            print(f"⚠️  Warning: Could not update blogs.html: {e}")

    def update_blog_post_image(self, slug: str, new_image: str):
        """Update image reference in individual blog post HTML"""
        blog_file_path = self.blogs_dir / f"{slug}.html"
        
        if not blog_file_path.exists():
            print(f"⚠️  Warning: Blog file {blog_file_path} not found")
            return
        
        try:
            with open(blog_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update the featured image - handle both existing image and no image cases
            import re
            
            if new_image and new_image.strip():
                # Create new image tag
                new_image_html = f'                <img src="../images/{new_image}" alt="" class="blog-featured-image">'
                
                # Try to replace existing image first
                pattern = r'<img src="../images/[^"]*" alt="[^"]*" class="blog-featured-image">'
                if re.search(pattern, content):
                    updated_content = re.sub(pattern, new_image_html, content)
                else:
                    # Replace no-image comment with image tag
                    comment_pattern = r'                <!-- No featured image -->'
                    updated_content = re.sub(comment_pattern, new_image_html, content)
            else:
                # Remove image, replace with comment
                pattern = r'<img src="../images/[^"]*" alt="[^"]*" class="blog-featured-image">'
                replacement = '                <!-- No featured image -->'
                updated_content = re.sub(pattern, replacement, content)
            
            with open(blog_file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
                
        except Exception as e:
            print(f"⚠️  Warning: Could not update {blog_file_path}: {e}")
    
    def run_single_mode(self):
        """Single PDF interactive mode"""
        while True:
            pdf_path = self.select_pdf_interactive()
            
            if pdf_path is None:
                print("\n👋 Goodbye!")
                break
            
            success = self.process_single_pdf(pdf_path)
            
            if success:
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
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()