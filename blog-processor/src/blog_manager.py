#!/usr/bin/env python3
"""
Blog Manager - Cleanup and management utilities
"""

import json
import os
import re
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict
from datetime import datetime

from main import MantoothBlogProcessor

class BlogManager:
    def __init__(self):
        self.processor = MantoothBlogProcessor()
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
        except Exception as e:
            print(f"Error loading blog data: {e}")
            return {"posts": [], "totalPosts": 0}
    
    def find_duplicates(self) -> Dict[str, List[Dict]]:
        """Find duplicate blog posts by slug"""
        blog_data = self.get_existing_blogs()
        duplicates = defaultdict(list)
        
        for post in blog_data.get("posts", []):
            slug = post.get("slug", "")
            if slug:
                duplicates[slug].append(post)
        
        # Only return slugs that have more than one post
        return {slug: posts for slug, posts in duplicates.items() if len(posts) > 1}
    
    def clean_duplicates(self, keep_latest=True) -> int:
        """Remove duplicate entries, keeping only the latest or first"""
        blog_data = self.get_existing_blogs()
        duplicates = self.find_duplicates()
        
        if not duplicates:
            print("✅ No duplicates found!")
            return 0
        
        print(f"🔍 Found {len(duplicates)} blog slugs with duplicates:")
        for slug, posts in duplicates.items():
            print(f"  - {slug}: {len(posts)} copies")
        
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
                print(f"  🗑️  Removing duplicate: {post.get('title', 'Unknown')} ({post.get('createdAt', 'Unknown date')})")
        
        # Update blog data
        blog_data["posts"] = cleaned_posts
        blog_data["totalPosts"] = len(cleaned_posts)
        blog_data["lastUpdated"] = datetime.now().isoformat()
        
        # Save cleaned data
        with open(self.blog_data_path, 'w', encoding='utf-8') as f:
            json.dump(blog_data, f, indent=2)
        
        print(f"✅ Removed {removed_count} duplicate entries")
        return removed_count
    
    def rebuild_blogs_html(self):
        """Rebuild blogs.html from JSON data"""
        blog_data = self.get_existing_blogs()
        posts = blog_data.get("posts", [])
        
        if not posts:
            print("⚠️  No posts found to rebuild")
            return
        
        print(f"🔄 Rebuilding blogs.html with {len(posts)} posts...")
        
        # Read the template part of blogs.html
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
        
        # Generate blog items HTML
        blog_items = []
        for post in posts:
            tags_html = ' '.join([f'<span class="tag">{tag.title()}</span>' for tag in post.get('tags', [])])
            
            item_html = f'''                <!-- Blog Post - {post.get('title', 'Unknown')} -->
                <article class="blog-item clickable-card" data-tags="{','.join(post.get('tags', []))}" data-url="blog-processor/output/{post.get('fileName', '')}">
                    <img src="blog-processor/images/{post.get('featuredImage', '')}" alt="{post.get('title', '')}">
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
        
        print("✅ blogs.html rebuilt successfully")
    
    def get_published_blogs(self) -> Set[str]:
        """Get list of already published blog slugs"""
        blog_data = self.get_existing_blogs()
        return {post.get("slug", "") for post in blog_data.get("posts", []) if post.get("slug")}
    
    def is_blog_published(self, pdf_filename: str) -> bool:
        """Check if a blog from this PDF is already published"""
        title = self.processor.extract_title_from_filename(pdf_filename)
        slug = self.processor.generate_slug(title)
        published_slugs = self.get_published_blogs()
        return slug in published_slugs
    
    def delete_blog_files(self, slug: str) -> bool:
        """Delete HTML file for a specific blog"""
        try:
            html_file = self.blogs_dir / f"{slug}.html"
            if html_file.exists():
                html_file.unlink()
                print(f"🗑️  Deleted: {html_file}")
                return True
            else:
                print(f"⚠️  File not found: {html_file}")
                return False
        except Exception as e:
            print(f"❌ Error deleting {slug}: {e}")
            return False
    
    def cleanup_orphaned_files(self):
        """Remove HTML files that don't have corresponding JSON entries"""
        blog_data = self.get_existing_blogs()
        json_files = {post.get("fileName", "") for post in blog_data.get("posts", [])}
        
        # Find all HTML files in blogs directory
        if not self.blogs_dir.exists():
            print("⚠️  Blogs directory doesn't exist")
            return
        
        html_files = list(self.blogs_dir.glob("*.html"))
        orphaned = []
        
        for html_file in html_files:
            if html_file.name not in json_files:
                orphaned.append(html_file)
        
        if not orphaned:
            print("✅ No orphaned files found")
            return
        
        print(f"🔍 Found {len(orphaned)} orphaned HTML files:")
        for file in orphaned:
            print(f"  - {file.name}")
        
        confirm = input("\nDelete these orphaned files? (y/n): ").strip().lower()
        if confirm in ['y', 'yes']:
            for file in orphaned:
                try:
                    file.unlink()
                    print(f"🗑️  Deleted: {file.name}")
                except Exception as e:
                    print(f"❌ Error deleting {file.name}: {e}")
        else:
            print("❌ Cleanup cancelled")
    
    def full_cleanup(self):
        """Perform complete cleanup"""
        print("🧹 Starting full cleanup...")
        print("=" * 50)
        
        # Step 1: Clean duplicates
        print("\n1. Cleaning duplicate entries...")
        removed = self.clean_duplicates(keep_latest=True)
        
        # Step 2: Clean orphaned files
        print("\n2. Cleaning orphaned files...")
        self.cleanup_orphaned_files()
        
        # Step 3: Rebuild blogs.html
        print("\n3. Rebuilding blogs.html...")
        self.rebuild_blogs_html()
        
        print("\n" + "=" * 50)
        print("🎉 Cleanup complete!")
        
        # Show final stats
        blog_data = self.get_existing_blogs()
        total_posts = len(blog_data.get("posts", []))
        print(f"📊 Final stats: {total_posts} unique blog posts")

def main():
    """Interactive cleanup tool"""
    manager = BlogManager()
    
    print("🧹 Mantooth Blog Manager")
    print("=" * 30)
    
    while True:
        print("\nChoose an action:")
        print("1. Find duplicates")
        print("2. Clean duplicates (keep latest)")
        print("3. Clean duplicates (keep first)")
        print("4. Rebuild blogs.html")
        print("5. Clean orphaned files")
        print("6. Full cleanup")
        print("7. Show blog stats")
        print("q. Quit")
        
        choice = input("\nEnter choice: ").strip().lower()
        
        if choice == "1":
            duplicates = manager.find_duplicates()
            if duplicates:
                print(f"\n🔍 Found duplicates for {len(duplicates)} blog slugs:")
                for slug, posts in duplicates.items():
                    print(f"  - {slug}: {len(posts)} copies")
                    for post in posts:
                        print(f"    • {post.get('createdAt', 'Unknown date')}")
            else:
                print("\n✅ No duplicates found!")
        
        elif choice == "2":
            manager.clean_duplicates(keep_latest=True)
        
        elif choice == "3":
            manager.clean_duplicates(keep_latest=False)
        
        elif choice == "4":
            manager.rebuild_blogs_html()
        
        elif choice == "5":
            manager.cleanup_orphaned_files()
        
        elif choice == "6":
            manager.full_cleanup()
        
        elif choice == "7":
            blog_data = manager.get_existing_blogs()
            posts = blog_data.get("posts", [])
            print(f"\n📊 Blog Statistics:")
            print(f"  Total posts: {len(posts)}")
            
            # Count by slug
            slugs = set()
            for post in posts:
                slugs.add(post.get("slug", ""))
            print(f"  Unique slugs: {len(slugs)}")
            print(f"  Duplicates: {len(posts) - len(slugs)}")
            
        elif choice == "q":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()