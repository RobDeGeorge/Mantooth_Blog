#!/usr/bin/env python3
"""
Mantooth Blog Processor GUI
PySide6/QML interface for blog processing
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from PySide6.QtCore import QObject, Signal, Slot, Property, QAbstractListModel, QModelIndex, Qt, QUrl, QThread
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import qmlRegisterType, QmlElement
from PySide6.QtQuickControls2 import QQuickStyle

# Import our existing blog processor
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))  # Add src directory to path
from main import MantoothBlogProcessor
from blog_manager import BlogManager

QML_IMPORT_NAME = "BlogProcessor"
QML_IMPORT_MAJOR_VERSION = 1

@QmlElement
class BlogItem(QObject):
    """Individual blog item for the UI"""
    
    titleChanged = Signal()
    slugChanged = Signal()
    excerptChanged = Signal()
    tagsChanged = Signal()
    imagePathChanged = Signal()
    statusChanged = Signal()
    
    def __init__(self, pdf_path: str = "", parent=None):
        super().__init__(parent)
        self._title = ""
        self._slug = ""
        self._excerpt = ""
        self._tags = []
        self._image_path = ""
        self._status = "pending"  # pending, processing, completed, error
        self._pdf_path = pdf_path
        
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
            self.PdfPathRole: b"pdfPath"
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
        
        return None
    
    def addItem(self, item: BlogItem):
        self.beginInsertRows(QModelIndex(), len(self._items), len(self._items))
        self._items.append(item)
        self.endInsertRows()
    
    def clear(self):
        self.beginResetModel()
        self._items.clear()
        self.endResetModel()
    
    def getItem(self, index: int) -> Optional[BlogItem]:
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

class ProcessingThread(QThread):
    """Background thread for PDF processing"""
    
    progressUpdate = Signal(int, str)  # index, status
    itemProcessed = Signal(int, dict)  # index, blog_data
    finished = Signal()
    
    def __init__(self, processor: MantoothBlogProcessor, items: List[BlogItem]):
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
                
                # Generate blog data
                title = self.processor.extract_title_from_filename(pdf_path.name)
                slug = self.processor.generate_slug(title)
                content_html = self.processor.format_content_to_html(paragraphs)
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
                    'pdf_path': str(pdf_path)
                }
                
                self.itemProcessed.emit(i, blog_data)
                self.progressUpdate.emit(i, "completed")
                
            except Exception as e:
                print(f"Error processing {item.pdfPath}: {e}")
                self.progressUpdate.emit(i, "error")
        
        self.finished.emit()

@QmlElement
class BlogProcessorBackend(QObject):
    """Main backend controller for the blog processor UI"""
    
    statusChanged = Signal(str)
    progressChanged = Signal(int, int)  # current, total
    itemsChanged = Signal()
    processingFinished = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._status = "ready"
        self._processor = MantoothBlogProcessor()
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
        self.status = "scanning"
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
                
                # Check if already published and get existing data
                if slug in published_posts:
                    published_post = published_posts[slug]
                    item.title = published_post.get("title", title)
                    item.tags = published_post.get("tags", [])
                    item.status = "published"
                    item.excerpt = published_post.get("excerpt", "")
                    # Load existing featured image
                    item.imagePath = published_post.get("featuredImage", "")
                else:
                    item.title = title
                    item.tags = []
                    item.status = "pending"
                    item.excerpt = ""
                    item.imagePath = image_path
                
                item.slug = slug
                
                self._blog_model.addItem(item)
            
            published_count = len([item for item in range(self._blog_model.rowCount()) 
                                 if self._blog_model.getItem(item).status == "published"])
            
            self.status = f"found {len(pdfs)} PDFs ({published_count} already published)"
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
            
            # Update the post in JSON data
            updated = False
            for post in posts:
                if post.get("slug") == current_slug:
                    post["title"] = item.title
                    post["tags"] = item.tags
                    post["featuredImage"] = item.imagePath if item.imagePath else ""
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
                    self._processor.selected_pdf = pdf_path  # Set this for format_content_to_html
                    extraction_result = self._processor.extract_text_from_pdf(pdf_path)
                    if extraction_result:
                        paragraphs = extraction_result['paragraphs']
                        content_html = self._processor.format_content_to_html(paragraphs)
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
            print(f"Update error details: {e}")
            import traceback
            traceback.print_exc()
    
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
                        print(f"Error deleting {html_file}: {e}")
            
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
            
            # Update blogs.html
            self._processor.update_blogs_html(blog_data)
            
            # Update JSON data
            self._processor.update_blog_data_json([blog_data])
            
            item.excerpt = blog_data['excerpt']
            
        except Exception as e:
            print(f"Error finalizing blog {index}: {e}")
            item.status = "error"
    
    @Slot(result=list)
    def getAvailableImages(self):
        """Get list of available images from blog-processor/images folder"""
        try:
            available_images = self._processor.list_available_images()
            return available_images
        except Exception as e:
            print(f"Error getting available images: {e}")
            return []
    
    @Slot(str)
    def getProjectRoot(self):
        """Get the project root path for QML"""
        root_path = str(self._processor.project_root)
        print(f"Project root for QML: {root_path}")
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
        print(f"Image path for {imageName}: {file_url}")
        
        # Check if file exists
        if full_path.exists():
            print(f"✅ Image file exists: {full_path}")
        else:
            print(f"❌ Image file missing: {full_path}")
        
        return file_url
    
    @Slot(int, str)
    def updateItemImage(self, index, imageName):
        """Update the image for a specific blog item"""
        try:
            item = self._blog_model.getItem(index)
            if item:
                print(f"Setting imagePath to: {imageName} for item: {item.title}")
                item.imagePath = imageName
                
                # Notify the model that this item's data has changed
                model_index = self._blog_model.index(index, 0)
                self._blog_model.dataChanged.emit(model_index, model_index, [self._blog_model.ImagePathRole])
                
                self.status = f"Updated image for '{item.title}' to '{imageName}' - hit Update to apply to published blog"
        except Exception as e:
            print(f"Error updating item image: {e}")
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
            print(f"Error updating published blog image: {e}")
    
    @Slot()
    def _onProcessingFinished(self):
        """Handle completion of all processing"""
        self.status = "processing completed - refreshing..."
        self.processingFinished.emit()
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