#!/usr/bin/env python3
"""
Automated Blog Processor for GitHub Actions
Processes PDF + image submissions and generates blog posts
"""

import os
import json
import re
import html
from datetime import datetime
from pathlib import Path
import pdfplumber


class BlogProcessor:
    def __init__(self):
        self.repo_root = Path(os.getcwd())
        self.pending_dir = self.repo_root / "pending-blogs"
        self.output_dir = self.repo_root / "website" / "blog-processor" / "output"
        self.images_dir = self.repo_root / "website" / "blog-processor" / "images"
        self.blogs_html = self.repo_root / "website" / "blogs.html"
        self.blog_data_json = self.repo_root / "website" / "assets" / "data" / "blog-data.json"

    def generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug from title"""
        slug = title.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')

    def extract_text_from_pdf(self, pdf_path: Path) -> list[str]:
        """Extract paragraphs from PDF with better paragraph detection"""
        paragraphs = []

        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n\n"  # Add extra newline between pages

        # First, normalize line breaks and fix hyphenation
        full_text = re.sub(r'(\w)-\n(\w)', r'\1\2', full_text)  # Fix hyphenated words

        # Try multiple strategies to detect paragraphs

        # Strategy 1: Split on double newlines (standard paragraph breaks)
        if '\n\n' in full_text:
            raw_paragraphs = re.split(r'\n\s*\n', full_text)
        # Strategy 2: Split on lines that end with period followed by newline and capital letter
        else:
            # Join lines that don't end with sentence-ending punctuation
            lines = full_text.split('\n')
            rebuilt_paragraphs = []
            current_para = ""

            for line in lines:
                line = line.strip()
                if not line:
                    if current_para:
                        rebuilt_paragraphs.append(current_para)
                        current_para = ""
                    continue

                if current_para:
                    # Check if previous paragraph ended with sentence-ending punctuation
                    # and current line starts with capital (new paragraph)
                    if (current_para[-1] in '.!?"' and
                        line[0].isupper() and
                        len(current_para) > 200):  # Likely a paragraph break
                        rebuilt_paragraphs.append(current_para)
                        current_para = line
                    else:
                        current_para += " " + line
                else:
                    current_para = line

            if current_para:
                rebuilt_paragraphs.append(current_para)

            raw_paragraphs = rebuilt_paragraphs if rebuilt_paragraphs else [full_text]

        for para in raw_paragraphs:
            # Clean up the paragraph
            cleaned = para.strip()
            cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize whitespace

            if len(cleaned) > 50:  # Only keep substantial paragraphs
                paragraphs.append(cleaned)

        # If we still only got 1 paragraph and it's very long, try to split by sentences
        if len(paragraphs) == 1 and len(paragraphs[0]) > 1500:
            long_text = paragraphs[0]
            # Split into chunks of roughly 3-4 sentences
            sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', long_text)

            if len(sentences) > 4:
                paragraphs = []
                chunk = ""
                sentence_count = 0

                for sentence in sentences:
                    chunk += sentence + " "
                    sentence_count += 1

                    # Create paragraph every 3-5 sentences or if chunk is getting long
                    if sentence_count >= 4 or len(chunk) > 800:
                        paragraphs.append(chunk.strip())
                        chunk = ""
                        sentence_count = 0

                if chunk.strip():
                    paragraphs.append(chunk.strip())

        return paragraphs

    def format_date(self, date_str: str = None) -> tuple[str, str]:
        """Return (display_date, iso_date)"""
        if date_str:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                dt = datetime.now()
        else:
            dt = datetime.now()

        display = dt.strftime("%B %d, %Y")
        iso = dt.strftime("%Y-%m-%d")
        return display, iso

    def generate_blog_html(self, title: str, paragraphs: list[str],
                           image_filename: str, tags: list[str],
                           display_date: str) -> str:
        """Generate the individual blog post HTML"""

        # Escape HTML in content
        safe_title = html.escape(title)
        tag_html = "\n".join(f'                    <span class="tag">{html.escape(tag.strip().title())}</span>'
                            for tag in tags)

        paragraphs_html = "\n\n".join(
            f"                    <p>{html.escape(p)}</p>"
            for p in paragraphs
        )

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title} - Mantooth</title>
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
                <h2 class="blog-title">{safe_title}</h2>
                <p class="post-meta">Posted on {display_date}</p>

                <img data-src="../images/{image_filename}" alt="{safe_title}" class="blog-featured-image lazy-loading">

                <div class="blog-content">
                    <h3>{safe_title}</h3>

{paragraphs_html}
                </div>

                <div class="blog-tags">
{tag_html}
                </div>
            </article>
        </div>
    </main>

    <footer>
        <div class="container">
            <p>&copy; {datetime.now().year} Mantooth. All Rights Reserved.</p>
            <div class="social-links">
                <a href="#">Facebook</a>
                <a href="#">Instagram</a>
            </div>
        </div>
    </footer>

    <script src="../../assets/js/image-optimizer.js"></script>
    <script src="../../assets/js/clickable-cards.js"></script>
</body>
</html>
'''

    def generate_blog_card_html(self, title: str, excerpt: str,
                                 image_filename: str, tags: list[str],
                                 display_date: str, slug: str) -> str:
        """Generate the blog card HTML for blogs.html"""

        safe_title = html.escape(title)
        safe_excerpt = html.escape(excerpt[:200] + "..." if len(excerpt) > 200 else excerpt)
        tags_data = ",".join(tag.lower().replace(" ", "-") for tag in tags)
        cache_bust = int(datetime.now().timestamp())

        tag_spans = " ".join(f'<span class="tag">{html.escape(tag.strip().title())}</span>'
                            for tag in tags)

        return f'''<!-- Blog Post - {safe_title} -->
                <article class="blog-item clickable-card" data-tags="{tags_data}" data-url="blog-processor/output/{slug}-blog.html">
                    <img data-src="blog-processor/images/{image_filename}?v={cache_bust}" alt="{safe_title}" class="lazy-loading">
                    <div class="blog-content">
                        <h3>{safe_title}</h3>
                        <p class="post-meta">Posted on {display_date}</p>
                        <p>{safe_excerpt}</p>
                        <div class="blog-footer">
                            <div class="blog-tags">
                                {tag_spans}
                            </div>
                        </div>
                    </div>
                </article>'''

    def update_blogs_html(self, card_html: str):
        """Insert new blog card at the top of the blog grid"""
        content = self.blogs_html.read_text(encoding='utf-8')

        # Find the blogs-grid section and insert after the opening tag
        insert_marker = '<section class="blogs-grid">'
        insert_pos = content.find(insert_marker)

        if insert_pos != -1:
            insert_pos += len(insert_marker)
            new_content = (
                content[:insert_pos] +
                f"                {card_html}\n" +
                content[insert_pos:]
            )
            self.blogs_html.write_text(new_content, encoding='utf-8')
            print(f"✓ Updated blogs.html")

    def update_blog_data_json(self, blog_data: dict):
        """Update the blog-data.json file"""
        if self.blog_data_json.exists():
            data = json.loads(self.blog_data_json.read_text(encoding='utf-8'))
        else:
            data = {"posts": [], "lastUpdated": "", "totalPosts": 0}

        # Add new post at the beginning
        data["posts"].insert(0, blog_data)
        data["lastUpdated"] = datetime.now().isoformat()
        data["totalPosts"] = len(data["posts"])

        # Ensure directory exists
        self.blog_data_json.parent.mkdir(parents=True, exist_ok=True)
        self.blog_data_json.write_text(json.dumps(data, indent=2), encoding='utf-8')
        print(f"✓ Updated blog-data.json")

    def find_pending_blog(self) -> tuple[Path | None, Path | None, dict]:
        """Find PDF and image in pending-blogs folder, along with metadata"""
        if not self.pending_dir.exists():
            print("No pending-blogs directory found")
            return None, None, {}

        pdf_file = None
        image_file = None
        metadata = {}

        # Look for files in pending-blogs
        for f in self.pending_dir.iterdir():
            if f.suffix.lower() == '.pdf':
                pdf_file = f
            elif f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                image_file = f
            elif f.name == 'metadata.json':
                metadata = json.loads(f.read_text(encoding='utf-8'))

        return pdf_file, image_file, metadata

    def process(self):
        """Main processing function"""
        print("🔍 Looking for pending blog posts...")

        pdf_file, image_file, file_metadata = self.find_pending_blog()

        if not pdf_file:
            print("No PDF found in pending-blogs/")
            return False

        if not image_file:
            print("No image found in pending-blogs/")
            return False

        # Get metadata from environment (manual trigger) or file
        title = os.environ.get('BLOG_TITLE') or file_metadata.get('title') or pdf_file.stem
        tags_str = os.environ.get('BLOG_TAGS') or file_metadata.get('tags') or 'blog'
        date_str = os.environ.get('BLOG_DATE') or file_metadata.get('date')

        tags = [t.strip() for t in tags_str.split(',')]
        slug = self.generate_slug(title)
        display_date, iso_date = self.format_date(date_str)

        print(f"📄 Processing: {title}")
        print(f"   Tags: {', '.join(tags)}")
        print(f"   Date: {display_date}")

        # Extract text from PDF
        paragraphs = self.extract_text_from_pdf(pdf_file)
        if not paragraphs:
            print("❌ Could not extract text from PDF")
            return False

        print(f"   Extracted {len(paragraphs)} paragraphs")

        # Move image to images directory with clean name
        new_image_name = f"{slug}{image_file.suffix.lower()}"
        dest_image = self.images_dir / new_image_name

        # Copy image
        dest_image.write_bytes(image_file.read_bytes())
        print(f"✓ Copied image to {dest_image}")

        # Generate blog post HTML
        blog_html = self.generate_blog_html(
            title=title,
            paragraphs=paragraphs,
            image_filename=new_image_name,
            tags=tags,
            display_date=display_date
        )

        # Save blog post
        blog_file = self.output_dir / f"{slug}-blog.html"
        blog_file.write_text(blog_html, encoding='utf-8')
        print(f"✓ Created {blog_file}")

        # Generate and insert blog card
        excerpt = paragraphs[0] if paragraphs else ""
        card_html = self.generate_blog_card_html(
            title=title,
            excerpt=excerpt,
            image_filename=new_image_name,
            tags=tags,
            display_date=display_date,
            slug=slug
        )
        self.update_blogs_html(card_html)

        # Update blog-data.json
        blog_data = {
            "id": f"{slug}-{datetime.now().year}",
            "title": title,
            "slug": f"{slug}-blog",
            "publishDate": iso_date,
            "excerpt": excerpt[:200] + "..." if len(excerpt) > 200 else excerpt,
            "featuredImage": new_image_name,
            "tags": tags,
            "readTime": max(1, len(" ".join(paragraphs).split()) // 200),
            "fileName": f"{slug}-blog.html",
            "createdAt": datetime.now().isoformat(),
            "source": "GitHub Actions"
        }
        self.update_blog_data_json(blog_data)

        # Clean up pending-blogs folder
        for f in self.pending_dir.iterdir():
            f.unlink()
        print(f"✓ Cleaned up pending-blogs/")

        # Set output for GitHub Actions
        github_output = os.environ.get('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a') as f:
                f.write(f"blog_title={title}\n")

        print(f"\n✅ Successfully published: {title}")
        return True


if __name__ == "__main__":
    processor = BlogProcessor()
    success = processor.process()
    exit(0 if success else 1)
