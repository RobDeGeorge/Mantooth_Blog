// blog-admin.js - Updated to reflect changes
class BlogAdmin {
    constructor() {
        this.generator = new BlogGenerator();
        this.setupForm();
        this.loadExistingPosts();
    }

    setupForm() {
        const form = document.getElementById('blogForm');
        const tagsInput = document.getElementById('tags');
        const tagDisplay = document.getElementById('tagDisplay');

        // Real-time tag display
        tagsInput.addEventListener('input', (e) => {
            this.updateTagDisplay(e.target.value, tagDisplay);
        });

        // Set default date to today
        document.getElementById('publishDate').value = new Date().toISOString().split('T')[0];

        // Form submission
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.createBlogPost();
        });
    }

    createBlogPost() {
        const formData = new FormData(document.getElementById('blogForm'));
        
        const blogData = {
            title: formData.get('title'),
            excerpt: formData.get('excerpt'),
            content: formData.get('content'),
            featuredImage: formData.get('featuredImage') || 'placeholder.png',
            tags: formData.get('tags').split(',').map(tag => tag.trim()).filter(tag => tag),
            publishDate: formData.get('publishDate')
        };

        // Generate the blog
        const blog = this.generator.addBlogPost(blogData);
        
        // Show generated HTML
        this.displayGeneratedFiles(blog);
        
        // Reset form
        document.getElementById('blogForm').reset();
        document.getElementById('tagDisplay').innerHTML = '';
    }

    displayGeneratedFiles(blog) {
        const output = document.getElementById('output');
        const codeDisplay = document.getElementById('generatedCode');
        
        // Generate the individual blog post HTML
        const blogHTML = this.generator.generateBlogFiles(blog);
        
        codeDisplay.innerHTML = `
            <h4>1. Save this as: assests/Blogs/${blog.slug}.html</h4>
            <textarea readonly style="width: 100%; height: 300px; font-family: monospace; margin-bottom: 20px;">${blogHTML}</textarea>
            
            <h4>2. Add this to your blogs.html (in the blogs-grid section):</h4>
            <textarea readonly style="width: 100%; height: 200px; font-family: monospace; margin-bottom: 20px;">${this.generator.generateBlogItemHTML(blog)}</textarea>
            
            <h4>3. File Locations & Instructions:</h4>
            <ul style="background: #f5f5f5; padding: 15px; border-radius: 5px;">
                <li><strong>Blog Post File:</strong> assests/Blogs/${blog.slug}.html</li>
                <li><strong>Featured Image:</strong> assests/Images/${blog.featuredImage}</li>
                <li><strong>Update:</strong> blogs.html (add the blog item code above)</li>
                <li><strong>Note:</strong> Blog cards are now clickable - no read more button needed!</li>
                <li><strong>Capacity:</strong> Main page can hold up to 30 blog posts</li>
            </ul>
            
            <div style="background: #e8f5e8; padding: 15px; border-radius: 5px; margin-top: 15px;">
                <h4>✅ Your blog post "${blog.title}" is ready to publish!</h4>
                <p>The entire blog card is clickable - users can click anywhere on it to read the full post!</p>
            </div>
        `;
        
        output.style.display = 'block';
    }

    updateTagDisplay(tagsString, container) {
        const tags = tagsString.split(',').map(tag => tag.trim()).filter(tag => tag);
        container.innerHTML = tags.map(tag => 
            `<span class="tag-item">${tag}</span>`
        ).join('');
    }

    async loadExistingPosts() {
        try {
            const response = await fetch('assests/JSON/blog-data.json');
            const data = await response.json();
            this.generator.blogData = data.posts || [];
        } catch (error) {
            console.log('No existing blog data found, starting fresh');
        }
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    new BlogAdmin();
});