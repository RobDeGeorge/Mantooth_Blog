#!/usr/bin/env python3
"""
Mantooth Blog Processor - Server-side PDF processing
Reads configuration from JSON files and saves results properly organized
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed. Run: pip install pdfplumber")
    sys.exit(1)

class MantoothBlogProcessor:
    def __init__(self):
        # Auto-detect project root more reliably
        self.script_dir = Path(__file__).parent
        
        # Check if we're in the right location and find project root
        current_path = Path.cwd()
        script_path = Path(__file__).parent
        
        # Look for the project root by finding the directory with blogs.html
        potential_roots = [
            script_path.parent,  # If script is in python/ folder
            current_path,        # If running from project root
            current_path.parent, # If running from a subfolder
            script_path.parent.parent,  # If script is in nested folder
        ]
        
        self.project_root = None
        for root in potential_roots:
            if (root / "blogs.html").exists():
                self.project_root = root
                break
        
        if not self.project_root:
            # Try to find it by looking for the assests folder
            for root in potential_roots:
                if (root / "assests").exists():
                    self.project_root = root
                    break
        
        if not self.project_root:
            print("ERROR: Could not find project root. Please run from the main project directory.")
            print(f"Current working directory: {current_path}")
            print(f"Script location: {script_path}")
            sys.exit(1)
        
        print(f"✅ Project root found: {self.project_root}")
        
        # Define paths matching the folder structure
        self.raw_blogs_dir = self.project_root / "assests" / "Blogs" / "Raw Blogs"
        self.blogs_dir = self.project_root / "assests" / "Blogs"
        self.images_dir = self.project_root / "assests" / "Images"
        self.json_dir = self.project_root / "assests" / "JSON"
        self.js_dir = self.project_root / "assests" / "JS"
        self.css_dir = self.project_root / "assests" / "CSS"
        
        self.blogs_html_path = self.project_root / "blogs.html"
        self.config_path = self.json_dir / "processing-config.json"
        self.blog_data_path = self.json_dir / "blog-data.json"
        
        # Print paths for debugging
        print(f"📁 Raw Blogs directory: {self.raw_blogs_dir}")
        print(f"📁 Blogs output directory: {self.blogs_dir}")
        print(f"📁 JSON directory: {self.json_dir}")
        
        # Create directories if needed
        self.blogs_dir.mkdir(parents=True, exist_ok=True)
        self.json_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self.load_configuration()

    def load_configuration(self) -> Dict:
        """Load processing configuration from JSON file"""
        default_config = {
            "autoTags": True,
            "autoExcerpts": True,
            "updateBlogsPage": True,
            "maxExcerptLength": 200,
            "maxTagsPerPost": 6
        }
        
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.log("Configuration loaded from assests/JSON/processing-config.json")
                return {**default_config, **config}
            else:
                self.log("Using default configuration")
                return default_config
        except Exception as e:
            self.log(f"Error loading config: {e}", "ERROR")
            return default_config

    def save_configuration(self):
        """Save current configuration to JSON file"""
        try:
            self.config['lastUpdated'] = datetime.now().isoformat()
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            self.log("Configuration saved to assests/JSON/processing-config.json")
        except Exception as e:
            self.log(f"Error saving config: {e}", "ERROR")

    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def extract_text_from_pdf(self, pdf_path: Path) -> Optional[str]:
        """Extract text from PDF using pdfplumber"""
        self.log(f"📄 Extracting text from: {pdf_path.name}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n\n"
                
                if not full_text.strip():
                    raise ValueError("No text content found")
                
                self.log(f"✅ Extracted {len(full_text)} characters from {pdf_path.name}")
                return full_text.strip()
                
        except Exception as e:
            self.log(f"❌ Error extracting from {pdf_path.name}: {e}", "ERROR")
            return None

    def clean_text(self, raw_text: str) -> str:
        """Clean and format extracted text"""
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', raw_text)
        
        # Fix paragraph breaks
        cleaned = re.sub(r'([.!?])\s*([A-Z])', r'\1\n\n\2', cleaned)
        
        # Remove common PDF artifacts
        cleaned = re.sub(r'Page \d+', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\f', '\n\n', cleaned)
        
        return cleaned.strip()

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
        paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 50]
        
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
        
        return content[:max_length] + "..." if len(content) > max_length else content

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
            'renaissance festival': ['renaissance', 'ren fest', 'festival']
        }
        
        for tag, keywords in location_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                suggested_tags.append(tag)
        
        # Activity tags
        activity_keywords = {
            'food': ['restaurant', 'food', 'eat', 'dining'],
            'restaurants': ['restaurant', 'dining', 'eatery'],
            'cocktails': ['cocktail', 'drink', 'bar'],
            'music': ['music', 'concert', 'band'],
            'concerts': ['concert', 'live music'],
            'travel': ['travel', 'trip', 'vacation'],
            'hiking': ['hike', 'hiking', 'trail'],
            'events': ['festival', 'event'],
            'pets': ['cat', 'pet', 'animal'],
            'cats': ['cat', 'feline', 'kitty']
        }
        
        for tag, keywords in activity_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                suggested_tags.append(tag)
        
        suggested_tags.append('lifestyle')
        
        max_tags = self.config.get('maxTagsPerPost', 6)
        return list(dict.fromkeys(suggested_tags))[:max_tags]

    def format_content_to_html(self, content: str) -> str:
        """Convert text to HTML paragraphs"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        return '\n\n'.join([f"                    <p>{para}</p>" for para in paragraphs])

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
    
    <!-- Load scripts from proper JS folder -->
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

    def update_blogs_html(self, new_blogs: List[Dict]) -> bool:
        """Update blogs.html with new entries"""
        if not self.config.get('updateBlogsPage', True):
            self.log("Skipping blogs.html update (disabled in config)")
            return True
            
        self.log(f"📝 Updating blogs.html with {len(new_blogs)} new posts")
        
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
            
            # Generate new blog items
            new_items = []
            for blog in new_blogs:
                item_html = f'''                <!-- Blog Post - {blog['title']} -->
                <article class="blog-item clickable-card" data-tags="{','.join(blog['tags'])}" data-url="assests/Blogs/{blog['slug']}.html">
                    <img src="assests/Images/{blog['featured_image']}" alt="{blog['title']}">
                    <div class="blog-content">
                        <h3>{blog['title']}</h3>
                        <p class="post-meta">Posted on {blog['formatted_date']}</p>
                        <p>{blog['excerpt']}</p>
                        <div class="blog-footer">
                            <div class="blog-tags">
                                {' '.join([f'<span class="tag">{tag.title()}</span>' for tag in blog['tags']])}
                            </div>
                        </div>
                    </div>
                </article>'''
                new_items.append(item_html)
            
            # Insert new items at beginning of grid
            existing_section = content[grid_start:grid_end + 10]
            insertion_point = existing_section.find('>', existing_section.find('<section class="blogs-grid">')) + 1
            
            new_content = '\n'.join(new_items)
            updated_section = (existing_section[:insertion_point] + 
                              '\n' + new_content + '\n                \n' + 
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

    def update_blog_data_json(self, new_blogs: List[Dict]):
        """Update blog-data.json in the JSON folder"""
        self.log("📊 Updating blog-data.json")
        
        # Load existing data
        if self.blog_data_path.exists():
            try:
                with open(self.blog_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except:
                data = {"posts": []}
        else:
            data = {"posts": []}
        
        # Add new posts to the beginning
        for blog in reversed(new_blogs):  # Reverse to maintain order
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
                "source": "PDF Processing"
            }
            data["posts"].insert(0, post_data)
        
        # Add metadata
        data["lastUpdated"] = datetime.now().isoformat()
        data["totalPosts"] = len(data["posts"])
        
        # Save updated data to JSON folder
        try:
            with open(self.blog_data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            self.log(f"✅ Updated {self.blog_data_path}")
        except Exception as e:
            self.log(f"❌ Error saving blog data: {e}", "ERROR")

    def save_processing_log(self, processed_blogs: List[Dict]):
        """Save processing log to JSON folder"""
        log_path = self.json_dir / "processing-log.json"
        
        # Load existing logs
        if log_path.exists():
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except:
                logs = {"sessions": []}
        else:
            logs = {"sessions": []}
        
        # Create new log entry
        session_log = {
            "timestamp": datetime.now().isoformat(),
            "blogsProcessed": len(processed_blogs),
            "files": [
                {
                    "title": blog['title'],
                    "slug": blog['slug'],
                    "htmlFile": f"assests/Blogs/{blog['slug']}.html",
                    "imageNeeded": f"assests/Images/{blog['featured_image']}",
                    "tags": blog['tags']
                }
                for blog in processed_blogs
            ],
            "configuration": self.config
        }
        
        logs["sessions"].insert(0, session_log)
        
        # Keep only last 50 sessions
        logs["sessions"] = logs["sessions"][:50]
        logs["lastUpdated"] = datetime.now().isoformat()
        
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2)
            self.log(f"📝 Processing log saved to {log_path}")
        except Exception as e:
            self.log(f"❌ Error saving processing log: {e}", "ERROR")

    def calculate_read_time(self, content: str) -> int:
        """Calculate estimated reading time in minutes"""
        # Remove HTML tags for word count
        text = re.sub(r'<[^>]+>', '', content)
        words = len(text.split())
        return max(1, round(words / 200))  # 200 words per minute

    def process_all_pdfs(self):
        """Main processing method"""
        if not self.raw_blogs_dir.exists():
            self.log(f"❌ Raw Blogs directory not found: {self.raw_blogs_dir}", "ERROR")
            self.log(f"💡 Please create the directory: {self.raw_blogs_dir}")
            return
        
        pdf_files = list(self.raw_blogs_dir.glob("*.pdf"))
        if not pdf_files:
            self.log(f"📂 No PDF files found in {self.raw_blogs_dir}")
            self.log(f"💡 Please add PDF files to: {self.raw_blogs_dir}")
            return
        
        self.log(f"🚀 Found {len(pdf_files)} PDF files to process")
        self.log(f"📁 Output directory: {self.blogs_dir}")
        self.log(f"📊 JSON data directory: {self.json_dir}")
        
        processed_blogs = []
        
        for pdf_path in pdf_files:
            self.log(f"🔄 Processing {pdf_path.name}")
            
            # Extract and process
            raw_text = self.extract_text_from_pdf(pdf_path)
            if not raw_text:
                continue
            
            cleaned_text = self.clean_text(raw_text)
            title = self.extract_title_from_filename(pdf_path.name)
            slug = self.generate_slug(title)
            excerpt = self.generate_excerpt(cleaned_text)
            tags = self.suggest_tags(title, cleaned_text)
            content_html = self.format_content_to_html(cleaned_text)
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
                'formatted_date': datetime.now().strftime("%B %d, %Y")
            }
            
            # Generate and save HTML to Blogs folder
            blog_html = self.create_blog_html(blog_data)
            blog_file_path = self.blogs_dir / f"{slug}.html"
            
            try:
                with open(blog_file_path, 'w', encoding='utf-8') as f:
                    f.write(blog_html)
                self.log(f"✅ Created: {blog_file_path}")
                
                # Check if image exists
                image_path = self.images_dir / featured_image
                if not image_path.exists():
                    self.log(f"⚠️  Image needed: {featured_image} (add to assests/Images/)")
                
                processed_blogs.append(blog_data)
                
            except Exception as e:
                self.log(f"❌ Error creating {blog_file_path}: {e}", "ERROR")
        
        if processed_blogs:
            # Update blogs.html
            self.update_blogs_html(processed_blogs)
            
            # Update JSON data in JSON folder
            self.update_blog_data_json(processed_blogs)
            
            # Save processing log to JSON folder
            self.save_processing_log(processed_blogs)
            
            # Update configuration
            self.save_configuration()
            
            self.log(f"🎉 Successfully processed {len(processed_blogs)} blog posts!")
            
            # Print summary
            print("\n" + "="*60)
            print("📋 PROCESSING COMPLETE!")
            print("="*60)
            print(f"📁 Blog files saved to: {self.blogs_dir}")
            print(f"📊 Data files saved to: {self.json_dir}")
            print(f"🖼️  Images needed in: {self.images_dir}")
            print()
            
            for blog in processed_blogs:
                print(f"✅ {blog['title']}")
                print(f"   📄 HTML: assests/Blogs/{blog['slug']}.html")
                print(f"   🖼️  Image: assests/Images/{blog['featured_image']}")
                print(f"   🏷️  Tags: {', '.join(blog['tags'])}")
                print()
                
            print("📋 Updated Files:")
            print(f"   • blogs.html (main blog listing)")
            print(f"   • assests/JSON/blog-data.json (blog metadata)")
            print(f"   • assests/JSON/processing-log.json (processing history)")
            print(f"   • assests/JSON/processing-config.json (settings)")
            
        else:
            self.log("❌ No blogs were successfully processed", "ERROR")

def main():
    """Main entry point"""
    processor = MantoothBlogProcessor()
    processor.process_all_pdfs()

if __name__ == "__main__":
    main()