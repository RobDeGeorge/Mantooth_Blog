#!/usr/bin/env python3
"""
Mantooth Blog Processor - Interactive PDF processing
Enhanced with better paragraph detection using font analysis
"""

import os
import sys
import json
import re
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import Counter

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
            "autoExcerpts": True,
            "updateBlogsPage": True,
            "maxExcerptLength": 200,
            "preserveFormatting": True,
            "detectLinks": True,
            "minParagraphLength": 20,  # Minimum length for a paragraph
            "paragraphFontTolerance": 0.1  # Font size tolerance for paragraph detection
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
        """Extract text and metadata from PDF with font information"""
        self.log(f"📄 Extracting text from: {pdf_path.name}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                pages_data = []
                links = []
                all_words_with_font = []
                
                for page_num, page in enumerate(pdf.pages, 1):
                    self.log(f"   Processing page {page_num}/{len(pdf.pages)}")
                    
                    # Extract words with font information
                    words_with_font = page.extract_words(
                        extra_attrs=["fontname", "size"],
                        keep_blank_chars=False,
                        use_text_flow=False
                    )
                    
                    # Store for font analysis
                    all_words_with_font.extend(words_with_font)
                    
                    # Extract text with layout preservation
                    text = page.extract_text(layout=True, x_tolerance=3, y_tolerance=3)
                    if text:
                        full_text += text + "\n\n"
                        pages_data.append({
                            'page': page_num,
                            'text': text.strip(),
                            'char_count': len(text),
                            'words_with_font': words_with_font
                        })
                    
                    # Extract links/annotations
                    if self.config.get('detectLinks', True):
                        page_links = self.extract_links_from_page(page)
                        links.extend(page_links)
                
                if not full_text.strip():
                    raise ValueError("No text content found")
                
                # Analyze font usage
                font_analysis = self.analyze_fonts(all_words_with_font)
                
                result = {
                    'text': full_text.strip(),
                    'pages': pages_data,
                    'links': links,
                    'total_pages': len(pdf.pages),
                    'total_chars': len(full_text),
                    'font_analysis': font_analysis,
                    'words_with_font': all_words_with_font
                }
                
                self.log(f"✅ Extracted {len(full_text)} characters, {len(links)} links")
                return result
                
        except Exception as e:
            self.log(f"❌ Error extracting from {pdf_path.name}: {e}", "ERROR")
            return None

    def analyze_fonts(self, words_with_font: List[Dict]) -> Dict:
        """Analyze font usage to identify paragraph and header fonts"""
        font_counter = Counter()
        size_counter = Counter()
        
        for word in words_with_font:
            if 'fontname' in word and 'size' in word:
                # Count font+size combinations
                font_key = f"{word['fontname']}_{word['size']:.1f}"
                font_counter[font_key] += len(word['text'])
                size_counter[word['size']] += len(word['text'])
        
        # Most common font+size combination is likely body text
        most_common_font = font_counter.most_common(1)[0][0] if font_counter else None
        
        # Extract font name and size from the key
        if most_common_font:
            parts = most_common_font.rsplit('_', 1)
            body_font_name = parts[0]
            body_font_size = float(parts[1])
        else:
            body_font_name = None
            body_font_size = 12.0  # Default
        
        return {
            'body_font': most_common_font,
            'body_font_name': body_font_name,
            'body_font_size': body_font_size,
            'font_distribution': dict(font_counter.most_common(10)),
            'size_distribution': dict(size_counter.most_common(10))
        }

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

    def clean_and_format_text_enhanced(self, extraction_result: Dict) -> str:
        """Enhanced text cleaning using font information for better paragraph detection"""
        raw_text = extraction_result['text']
        font_analysis = extraction_result.get('font_analysis', {})
        words_with_font = extraction_result.get('words_with_font', [])
        links = extraction_result.get('links', [])
        
        # Get body font information
        body_font_size = font_analysis.get('body_font_size', 12.0)
        font_tolerance = self.config.get('paragraphFontTolerance', 0.1)
        
        # Step 1: Clean up obvious PDF artifacts
        cleaned = raw_text
        
        # Remove page numbers and headers/footers
        cleaned = re.sub(r'Page \d+.*?\n', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\n\s*\d+\s*\n', '\n', cleaned)  # Standalone page numbers
        cleaned = re.sub(r'\f', '\n\n', cleaned)  # Form feeds
        
        # Step 2: Split into lines and analyze each line's font properties
        lines = cleaned.split('\n')
        line_properties = []
        
        for line in lines:
            line_text = line.strip()
            if not line_text:
                line_properties.append({'text': '', 'is_header': False, 'font_size': body_font_size})
                continue
            
            # Find average font size for this line
            line_font_sizes = []
            for word in words_with_font:
                if word['text'] in line_text:
                    line_font_sizes.append(word.get('size', body_font_size))
            
            avg_font_size = sum(line_font_sizes) / len(line_font_sizes) if line_font_sizes else body_font_size
            
            # Determine if this line is likely a header
            is_header = self.is_likely_header_by_font(line_text, avg_font_size, body_font_size, font_tolerance)
            
            line_properties.append({
                'text': line_text,
                'is_header': is_header,
                'font_size': avg_font_size
            })
        
        # Step 3: Build paragraphs using font information
        paragraphs = []
        current_paragraph = []
        
        i = 0
        while i < len(line_properties):
            line_prop = line_properties[i]
            line_text = line_prop['text']
            
            if not line_text:  # Empty line
                if current_paragraph:
                    # End current paragraph
                    paragraph_text = ' '.join(current_paragraph).strip()
                    if len(paragraph_text) > self.config.get('minParagraphLength', 20):
                        paragraphs.append(paragraph_text)
                    current_paragraph = []
                i += 1
                continue
            
            # If this is a header, save current paragraph and add header
            if line_prop['is_header']:
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph).strip()
                    if len(paragraph_text) > self.config.get('minParagraphLength', 20):
                        paragraphs.append(paragraph_text)
                    current_paragraph = []
                
                # Add header as its own paragraph
                paragraphs.append(line_text)
                i += 1
                continue
            
            # Check if this line should start a new paragraph
            should_start_new = self.should_start_new_paragraph_enhanced(
                line_text, current_paragraph, line_properties, i
            )
            
            if should_start_new and current_paragraph:
                # Finish current paragraph
                paragraph_text = ' '.join(current_paragraph).strip()
                if len(paragraph_text) > self.config.get('minParagraphLength', 20):
                    paragraphs.append(paragraph_text)
                current_paragraph = [line_text]
            else:
                current_paragraph.append(line_text)
            
            i += 1
        
        # Don't forget the last paragraph
        if current_paragraph:
            paragraph_text = ' '.join(current_paragraph).strip()
            if len(paragraph_text) > self.config.get('minParagraphLength', 20):
                paragraphs.append(paragraph_text)
        
        # Step 4: Post-process paragraphs
        final_paragraphs = self.post_process_paragraphs(paragraphs)
        
        # Step 5: Convert URLs to markdown-style links if found
        if self.config.get('detectLinks', True) and links:
            for i, para in enumerate(final_paragraphs):
                final_paragraphs[i] = self.convert_links_to_markdown(para, links)
        
        return '\n\n'.join(final_paragraphs)

    def is_likely_header_by_font(self, text: str, font_size: float, body_font_size: float, tolerance: float) -> bool:
        """Determine if text is likely a header based on font size and other characteristics"""
        # Font size significantly larger than body text
        if font_size > body_font_size * (1 + tolerance):
            return True
        
        # Short text that doesn't end with sentence punctuation
        if len(text) < 100 and not text.endswith(('.', '!', '?', ',')):
            # Check for heading patterns
            heading_patterns = [
                r'^[A-Z][a-z]+.*:$',  # Title with colon
                r'^[A-Z][A-Z\s]+$',   # ALL CAPS
                r'^Chapter\s+\d+',    # Chapter
                r'^Section\s+\d+',    # Section
                r'^\d+\.\s+[A-Z]',    # Numbered heading
                r'^[A-Z][^.!?]{0,50}$'  # Short capitalized text without punctuation
            ]
            
            for pattern in heading_patterns:
                if re.match(pattern, text):
                    return True
        
        return False

    def should_start_new_paragraph_enhanced(self, line: str, current_paragraph: List[str], 
                                           line_properties: List[Dict], line_index: int) -> bool:
        """Enhanced paragraph detection using multiple signals"""
        
        # If no current paragraph, always start new
        if not current_paragraph:
            return True
        
        # Get current and previous line properties
        current_prop = line_properties[line_index]
        
        # If previous line was much shorter than average, might be paragraph end
        if current_paragraph:
            last_line = current_paragraph[-1]
            avg_line_length = sum(len(l) for l in current_paragraph) / len(current_paragraph)
            if len(last_line) < avg_line_length * 0.7:
                # Previous line was short, check if it ends with punctuation
                if re.search(r'[.!?]\s*$', last_line):
                    return True
        
        # Check for sentence endings in previous content
        last_line = current_paragraph[-1] if current_paragraph else ''
        
        # If last line ends with sentence punctuation and this line starts with capital
        if re.search(r'[.!?]\s*$', last_line) and re.match(r'^[A-Z]', line):
            # Check if there was a significant gap (empty line) before this
            if line_index > 0 and not line_properties[line_index - 1]['text']:
                return True
        
        # Check for topic changes (basic keyword analysis)
        current_text = ' '.join(current_paragraph).lower()
        line_lower = line.lower()
        
        # Topic change indicators
        topic_indicators = [
            'however', 'meanwhile', 'in contrast', 'on the other hand', 
            'furthermore', 'additionally', 'moreover', 'nevertheless',
            'in conclusion', 'to summarize', 'first', 'second', 'third',
            'finally', 'next', 'then'
        ]
        
        for indicator in topic_indicators:
            if line_lower.startswith(indicator):
                return True
        
        # Check for time/location transitions
        time_location_patterns = [
            r'^(yesterday|today|tomorrow|last\s+\w+|next\s+\w+)',
            r'^(in|at|on|from|during)\s+[A-Z]',
            r'^\d{4}|\d{1,2}[\/\-]\d{1,2}',  # Dates
        ]
        
        for pattern in time_location_patterns:
            if re.match(pattern, line_lower):
                return True
        
        # Check if this line is indented (starts with spaces)
        if line.startswith('    ') or line.startswith('\t'):
            return True
        
        return False

    def post_process_paragraphs(self, paragraphs: List[str]) -> List[str]:
        """Post-process paragraphs to fix common issues"""
        processed = []
        
        for para in paragraphs:
            # Fix sentence spacing
            para = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', para)
            
            # Remove extra spaces
            para = re.sub(r'\s+', ' ', para)
            
            # Trim
            para = para.strip()
            
            # Skip very short paragraphs unless they look like headers
            if len(para) < self.config.get('minParagraphLength', 20):
                if self.is_likely_header_by_font(para, 0, 0, 0):  # Using text patterns only
                    processed.append(para)
            else:
                processed.append(para)
        
        return processed

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
        paragraphs = content.split('\n\n')
        html_elements = []
        
        in_list = False
        list_items = []
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Check if this is a list item
            is_list_item = (
                re.match(r'^[•\-\*]\s+', para) or 
                re.match(r'^\d+[\.\)]\s+', para) or
                re.match(r'^[a-zA-Z][\.\)]\s+', para)
            )
            
            if is_list_item:
                if not in_list:
                    # Start a new list
                    if list_items:  # Close previous list if any
                        html_elements.append(self.format_list_items(list_items))
                        list_items = []
                    in_list = True
                
                # Clean up the list marker
                clean_item = re.sub(r'^[•\-\*\d+a-zA-Z][\.\)]\s*', '', para)
                list_items.append(clean_item)
            
            else:
                # Not a list item
                if in_list:
                    # Close the current list
                    html_elements.append(self.format_list_items(list_items))
                    list_items = []
                    in_list = False
                
                # Check if this might be a heading (using simple heuristics)
                if len(para) < 100 and not para.endswith(('.', '!', '?', ',')):
                    # Might be a heading
                    html_elements.append(f"                    <h3>{para}</h3>")
                else:
                    # Regular paragraph - convert markdown links to HTML
                    para_html = self.convert_markdown_links_to_html(para)
                    html_elements.append(f"                    <p>{para_html}</p>")
        
        # Don't forget to close any remaining list
        if in_list and list_items:
            html_elements.append(self.format_list_items(list_items))
        
        return '\n\n'.join(html_elements)

    def format_list_items(self, items: List[str]) -> str:
        """Format list items as HTML"""
        if not items:
            return ""
        
        html_items = []
        for item in items:
            item_html = self.convert_markdown_links_to_html(item)
            html_items.append(f"                        <li>{item_html}</li>")
        
        return "                    <ul>\n" + "\n".join(html_items) + "\n                    </ul>"

    def convert_markdown_links_to_html(self, text: str) -> str:
        """Convert markdown-style links to HTML"""
        # Pattern for [text](url)
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        
        def replace_link(match):
            link_text = match.group(1)
            url = match.group(2)
            return f'<a href="{url}" target="_blank" rel="noopener">{link_text}</a>'
        
        return re.sub(link_pattern, replace_link, text)

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
            # Try to find a good paragraph that's not a header
            for para in paragraphs:
                if not re.match(r'^[A-Z][A-Z\s]+$', para) and para.endswith(('.', '!', '?')):
                    if len(para) <= max_length:
                        return para
                    else:
                        excerpt = para[:max_length]
                        last_space = excerpt.rfind(' ')
                        if last_space > max_length * 0.8:
                            excerpt = excerpt[:last_space]
                        return excerpt + "..."
            
            # Fallback to first paragraph
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

    def get_tags_from_user(self, title: str, content: str) -> List[str]:
        """Get tags from user input"""
        print("\n🏷️  TAG SELECTION")
        print("-" * 40)
        print(f"Blog Title: {title}")
        print("\nPlease enter tags for this blog post.")
        print("Separate multiple tags with commas (e.g., phoenix, food, restaurants)")
        print("\nSuggested tag categories:")
        print("- Locations: phoenix, arizona, gatlinburg, los angeles")
        print("- Activities: food, restaurants, cocktails, music, concerts, travel, hiking")
        print("- General: lifestyle, events, reviews, pets")
        print("-" * 40)
        
        while True:
            tags_input = input("\nEnter tags: ").strip()
            
            if not tags_input:
                print("❌ Please enter at least one tag.")
                continue
            
            # Parse and clean tags
            tags = [tag.strip().lower() for tag in tags_input.split(',')]
            tags = [tag for tag in tags if tag]  # Remove empty tags
            
            if not tags:
                print("❌ No valid tags entered. Please try again.")
                continue
            
            # Show what was entered
            print(f"\n✅ Tags selected: {', '.join(tags)}")
            
            confirm = input("Are these tags correct? (y/n): ").strip().lower()
            
            if confirm in ['y', 'yes']:
                return tags
            elif confirm in ['n', 'no']:
                print("Let's try again...")
            else:
                print("Please enter 'y' for yes or 'n' for no")

    def generate_image_name(self, pdf_filename: str) -> str:
        """Generate image filename"""
        base_name = pdf_filename.replace('.pdf', '').lower()
        base_name = re.sub(r'[^a-z0-9]', '_', base_name)
        base_name = re.sub(r'_+', '_', base_name).strip('_')
        return f"{base_name}_blog.png"

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
        content_preview = blog_data['content'][:800]
        if len(blog_data['content']) > 800:
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
        print(f"\nCurrent tags: {current_tags}")
        print("Enter new tags separated by commas, or press Enter to keep current tags")
        new_tags = input("Tags: ").strip()
        if new_tags:
            blog_data['tags'] = [tag.strip().lower() for tag in new_tags.split(',')]
            blog_data['tags'] = [tag for tag in blog_data['tags'] if tag]  # Remove empty
        
        # Edit excerpt
        print(f"\nCurrent excerpt:\n{blog_data['excerpt']}")
        new_excerpt = input("\nNew excerpt (or press Enter to keep): ").strip()
        if new_excerpt:
            blog_data['excerpt'] = new_excerpt
        
        # Edit image filename
        new_image = input(f"\nImage filename [{blog_data['featured_image']}]: ").strip()
        if new_image:
            # Ensure it ends with an image extension
            if not re.search(r'\.(png|jpg|jpeg|gif|webp)$', new_image, re.IGNORECASE):
                new_image += '.png'
            blog_data['featured_image'] = new_image

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
        
        # Use enhanced text cleaning with font analysis
        cleaned_text = self.clean_and_format_text_enhanced(extraction_result)
        
        # Extract title and generate initial data
        title = self.extract_title_from_filename(pdf_path.name)
        slug = self.generate_slug(title)
        content_html = self.format_content_to_html(cleaned_text)
        excerpt = self.generate_excerpt(content_html)
        featured_image = self.generate_image_name(pdf_path.name)
        
        # Get tags from user
        tags = self.get_tags_from_user(title, cleaned_text)
        
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
            'links_found': len(extraction_result.get('links', [])),
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
            if extraction_result.get('links'):
                print(f"🔗 Links found: {len(extraction_result['links'])}")
            
            # Show paragraph statistics
            paragraphs = cleaned_text.split('\n\n')
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
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()