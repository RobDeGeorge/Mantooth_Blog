// blog-generator.js - Updated to remove read more buttons and increase capacity
class BlogGenerator {
    constructor() {
        this.blogData = [];
        this.maxPostsPerPage = 30; // Increased from 6 to 30
        this.templates = {
            blogItem: this.getBlogItemTemplate(),
            blogPost: this.getBlogPostTemplate()
        };
    }

    // Add new blog post
    addBlogPost(postData) {
        const blog = {
            id: this.generateId(postData.title),
            title: postData.title,
            slug: this.createSlug(postData.title),
            author: postData.author || 'Ella',
            publishDate: postData.publishDate || new Date().toISOString().split('T')[0],
            excerpt: postData.excerpt,
            content: postData.content,
            featuredImage: postData.featuredImage,
            tags: postData.tags || [],
            readTime: this.calculateReadTime(postData.content)
        };

        this.blogData.push(blog);
        this.generateBlogFiles(blog);
        this.updateBlogsPage();
        return blog;
    }

    // Generate individual blog HTML file
    generateBlogFiles(blog) {
        const blogHTML = this.templates.blogPost
            .replace(/{{title}}/g, blog.title)
            .replace(/{{publishDate}}/g, this.formatDate(blog.publishDate))
            .replace(/{{featuredImage}}/g, blog.featuredImage)
            .replace(/{{content}}/g, blog.content)
            .replace(/{{tags}}/g, this.generateTagsHTML(blog.tags))
            .replace(/{{slug}}/g, blog.slug);

        console.log(`Generated: assests/Blogs/${blog.slug}.html`);
        return blogHTML;
    }

    // Generate blog item for blogs.html (updated - no read more button, clickable card, lazy loading)
    generateBlogItemHTML(blog) {
        return `
            <article class="blog-item clickable-card" data-tags="${blog.tags.join(',')}" data-url="assests/Blogs/${blog.slug}.html">
                <img data-src="assests/Images/${blog.featuredImage}" alt="${blog.title}" class="lazy-loading">
                <div class="blog-content">
                    <h3>${blog.title}</h3>
                    <p class="post-meta">Posted on ${this.formatDate(blog.publishDate)}</p>
                    <p>${blog.excerpt}</p>
                    <div class="blog-footer">
                        <div class="blog-tags">
                            ${blog.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                        </div>
                    </div>
                </div>
            </article>
        `;
    }

    // Updated blog post template for your file structure
    getBlogPostTemplate() {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}} - Mantooth</title>
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
                <h2 class="blog-title">{{title}}</h2>
                <p class="post-meta">Posted on {{publishDate}}</p>
                
                <img data-src="../Images/{{featuredImage}}" alt="{{title}}" class="blog-featured-image lazy-loading">
                
                <div class="blog-content">
                    {{content}}
                </div>
                
                <div class="blog-tags">
                    {{tags}}
                </div>
            </article>
        </div>
    </main>

    <footer>
        <div class="container">
            <p>&copy; 2026 Mantooth. All Rights Reserved.</p>
            <div class="social-links">
                <a href="https://www.instagram.com/mantooth.meblog/">Instagram</a>
            </div>
        </div>
    </footer>

    <script src="../../assets/js/image-optimizer.js"></script>
    <script src="../../assets/js/clickable-cards.js"></script>
</body>
</html>`;
    }

    generateId(title) {
        return title.toLowerCase().replace(/[^a-z0-9]/g, '-').replace(/-+/g, '-').trim('-');
    }

    createSlug(title) {
        return title.toLowerCase()
            .replace(/[^a-z0-9\s-]/g, '')
            .replace(/\s+/g, '-')
            .replace(/-+/g, '-')
            .trim('-') + '-blog';
    }

    calculateReadTime(content) {
        const wordsPerMinute = 200;
        const wordCount = content.split(' ').length;
        return Math.ceil(wordCount / wordsPerMinute);
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
    }

    generateTagsHTML(tags) {
        return tags.map(tag => `<span class="tag">${tag}</span>`).join('');
    }

    updateBlogsPage() {
        const blogsGrid = document.querySelector('.blogs-grid');
        if (!blogsGrid) return;

        blogsGrid.innerHTML = '';
        this.blogData.forEach(blog => {
            const blogItemHTML = this.generateBlogItemHTML(blog);
            blogsGrid.insertAdjacentHTML('beforeend', blogItemHTML);
        });
        
        // Initialize lazy loading for new images
        if (window.imageOptimizer) {
            window.imageOptimizer.initializePageImages();
        }
    }
}