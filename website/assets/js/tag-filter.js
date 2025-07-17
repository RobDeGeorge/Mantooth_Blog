// tag-filter.js - Updated for your file structure
class TagFilter {
    constructor() {
        this.createFilterButtons();
        this.bindEvents();
    }

    createFilterButtons() {
        const blogsHeader = document.querySelector('.blogs-header');
        if (!blogsHeader) return;

        // Get all unique tags from existing blog items
        const allTags = this.extractTagsFromPage();
        
        if (allTags.length === 0) return; // No tags found

        // Create filter container
        const filterContainer = document.createElement('div');
        filterContainer.className = 'tag-filter-container';
        filterContainer.style.cssText = `
            margin-top: 20px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        `;

        // All button
        const allButton = this.createButton('all', 'All Posts', true);
        filterContainer.appendChild(allButton);

        // Tag buttons
        allTags.forEach(tag => {
            const button = this.createButton(tag, tag.charAt(0).toUpperCase() + tag.slice(1));
            filterContainer.appendChild(button);
        });

        blogsHeader.appendChild(filterContainer);
    }

    createButton(tag, label, isActive = false) {
        const button = document.createElement('button');
        button.className = `tag-filter ${isActive ? 'active' : ''}`;
        button.dataset.tag = tag;
        button.textContent = label;
        
        // Use your existing button styles from style.css
        button.style.cssText = `
            background: ${isActive ? '#F18F01' : 'rgba(255,255,255,0.8)'};
            border: 2px solid #F18F01;
            border-radius: 20px;
            padding: 8px 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: capitalize;
            color: ${isActive ? 'white' : '#2D4059'};
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
        `;

        return button;
    }

    extractTagsFromPage() {
        const blogItems = document.querySelectorAll('.blog-item');
        const allTags = new Set();

        console.log('Found blog items:', blogItems.length);

        blogItems.forEach((item, index) => {
            const tags = item.dataset.tags;
            console.log(`Blog item ${index} tags:`, tags);
            if (tags) {
                tags.split(',').forEach(tag => {
                    const cleanTag = tag.trim().toLowerCase();
                    if (cleanTag) allTags.add(cleanTag);
                });
            }
        });

        const tagArray = Array.from(allTags).sort();
        console.log('All extracted tags:', tagArray);
        return tagArray;
    }

    bindEvents() {
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tag-filter')) {
                this.handleFilter(e.target);
            }
        });
    }

    handleFilter(button) {
        const selectedTag = button.dataset.tag;
        
        // Update button states
        document.querySelectorAll('.tag-filter').forEach(btn => {
            btn.classList.remove('active');
            btn.style.background = 'rgba(255,255,255,0.8)';
            btn.style.color = '#2D4059';
        });
        
        button.classList.add('active');
        button.style.background = '#F18F01';
        button.style.color = 'white';

        // Filter posts
        this.filterPosts(selectedTag);
        
        // Update results info
        this.updateResultsInfo(selectedTag);
    }

    filterPosts(selectedTag) {
        const blogItems = document.querySelectorAll('.blog-item');
        let visibleCount = 0;
        
        blogItems.forEach(item => {
            const itemTags = item.dataset.tags ? 
                item.dataset.tags.split(',').map(tag => tag.trim().toLowerCase()) : [];
            
            const shouldShow = selectedTag === 'all' || 
                              itemTags.includes(selectedTag.toLowerCase());
            
            if (shouldShow) {
                item.style.display = 'flex';
                item.style.opacity = '1';
                visibleCount++;
                // Add fade-in animation
                item.style.animation = 'fadeIn 0.5s ease-in';
            } else {
                item.style.display = 'none';
            }
        });

        return visibleCount;
    }

    updateResultsInfo(selectedTag) {
        let resultText = document.querySelector('.filter-results-info');
        
        if (!resultText) {
            resultText = document.createElement('p');
            resultText.className = 'filter-results-info';
            resultText.style.cssText = `
                text-align: center;
                margin: 20px 0;
                color: #666;
                font-style: italic;
            `;
            
            const blogsGrid = document.querySelector('.blogs-grid');
            if (blogsGrid) {
                blogsGrid.parentNode.insertBefore(resultText, blogsGrid);
            }
        }

        const visibleCount = this.filterPosts(selectedTag);
        
        if (selectedTag === 'all') {
            resultText.textContent = `Showing all ${visibleCount} posts`;
        } else {
            resultText.textContent = `Showing ${visibleCount} posts tagged with "${selectedTag}"`;
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if we're on the blogs page
    if (document.querySelector('.blogs-grid')) {
        // Add a small delay to ensure all elements are ready
        setTimeout(() => {
            const tagFilter = new TagFilter();
            console.log('TagFilter initialized with tags:', tagFilter.extractTagsFromPage());
        }, 100);
    }
});