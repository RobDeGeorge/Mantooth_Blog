// recent-posts.js
class RecentPostsManager {
    constructor() {
        this.maxRecentPosts = 3;
    }

    async loadRecentPosts() {
        try {
            // Fetch the blogs.html page
            const response = await fetch('blogs.html');
            const html = await response.text();
            
            // Parse the HTML
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Extract blog posts
            const blogPosts = this.extractBlogPosts(doc);
            
            // Sort by date (most recent first)
            const sortedPosts = this.sortPostsByDate(blogPosts);
            
            // Get the most recent posts
            const recentPosts = sortedPosts.slice(0, this.maxRecentPosts);
            
            // Render the posts
            this.renderRecentPosts(recentPosts);
            
        } catch (error) {
            console.error('Error loading recent posts:', error);
            this.showErrorMessage();
        }
    }

    extractBlogPosts(doc) {
        const blogItems = doc.querySelectorAll('.blog-item');
        const posts = [];

        blogItems.forEach(item => {
            const title = item.querySelector('h3')?.textContent.trim();
            const excerpt = item.querySelector('.blog-content > p:not(.post-meta)')?.textContent.trim();
            const dateText = item.querySelector('.post-meta')?.textContent.trim();
            const image = item.querySelector('img')?.src || item.querySelector('img')?.getAttribute('src');
            const url = item.getAttribute('data-url');
            const tags = item.getAttribute('data-tags')?.split(',') || [];

            // Parse date from "Posted on Month Day, Year" format
            const date = this.parseDate(dateText);

            if (title && excerpt && url) {
                posts.push({
                    title,
                    excerpt: this.truncateExcerpt(excerpt),
                    date,
                    dateText,
                    image,
                    url,
                    tags
                });
            }
        });

        return posts;
    }

    parseDate(dateText) {
        if (!dateText) return new Date(0);
        
        // Extract date from "Posted on Month Day, Year" format
        const match = dateText.match(/Posted on (.+)/);
        if (match) {
            return new Date(match[1]);
        }
        return new Date(0);
    }

    sortPostsByDate(posts) {
        return posts.sort((a, b) => b.date - a.date);
    }

    truncateExcerpt(text, maxLength = 150) {
        if (text.length <= maxLength) return text;
        return text.substr(0, maxLength).split(' ').slice(0, -1).join(' ') + '...';
    }

    renderRecentPosts(posts) {
        const container = document.getElementById('recent-posts-container');
        
        if (posts.length === 0) {
            container.innerHTML = '<p class="no-posts">No blog posts found.</p>';
            return;
        }

        const postsHTML = posts.map(post => `
            <article class="post-card clickable-card" data-url="${post.url}">
                ${post.image ? `<img src="${post.image}" alt="${post.title}">` : '<div class="no-image-placeholder"></div>'}
                <h3>${post.title}</h3>
                <p class="post-meta">${post.dateText}</p>
                <p>${post.excerpt}</p>
            </article>
        `).join('');

        container.innerHTML = postsHTML;
        
        // Re-initialize clickable cards functionality
        this.initializeClickableCards();
    }

    initializeClickableCards() {
        // Re-run the clickable cards script for the new elements
        const cards = document.querySelectorAll('#recent-posts-container .clickable-card');
        cards.forEach(card => {
            card.addEventListener('click', function() {
                const url = this.getAttribute('data-url');
                if (url) {
                    window.location.href = url;
                }
            });
        });
    }

    showErrorMessage() {
        const container = document.getElementById('recent-posts-container');
        container.innerHTML = '<p class="error-message">Unable to load recent posts. Please try again later.</p>';
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const recentPostsManager = new RecentPostsManager();
    recentPostsManager.loadRecentPosts();
});