// Image optimization and lazy loading utilities
class ImageOptimizer {
    constructor() {
        this.lazyImages = [];
        this.imageObserver = null;
        this.preloadedImages = new Map();
        this.initializeLazyLoading();
    }

    // Initialize Intersection Observer for lazy loading
    initializeLazyLoading() {
        if ('IntersectionObserver' in window) {
            this.imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        this.loadImage(img);
                        observer.unobserve(img);
                    }
                });
            }, {
                // Load images when they're 200px from entering viewport
                rootMargin: '200px'
            });
        }
    }

    // Add lazy loading to an image
    addLazyImage(img) {
        if (!img.dataset.src) return;
        
        // Add loading placeholder
        img.classList.add('lazy-loading');
        
        if (this.imageObserver) {
            this.imageObserver.observe(img);
        } else {
            // Fallback for browsers without IntersectionObserver
            this.loadImage(img);
        }
    }

    // Load an individual image
    loadImage(img) {
        const src = img.dataset.src;
        if (!src) return;

        // Create new image to preload
        const imageLoader = new Image();
        
        imageLoader.onload = () => {
            img.src = src;
            img.classList.remove('lazy-loading');
            img.classList.add('lazy-loaded');
            
            // Trigger fade-in animation
            img.style.opacity = '1';
        };
        
        imageLoader.onerror = () => {
            img.classList.remove('lazy-loading');
            img.classList.add('lazy-error');
            
            // Show error placeholder
            img.alt = 'Image failed to load';
            img.style.backgroundColor = '#f0f0f0';
        };
        
        imageLoader.src = src;
    }

    // Preload satellite images for home page
    preloadSatelliteImages() {
        const satImages = [
            'assets/images/Sat_photo_1.jpg',
            'assets/images/Sat_photo_2.jpg',
            'assets/images/Sat_photo_3.jpg'
        ];

        return Promise.all(
            satImages.map(src => this.preloadImage(src))
        );
    }

    // Preload a single image
    preloadImage(src) {
        return new Promise((resolve, reject) => {
            if (this.preloadedImages.has(src)) {
                resolve(this.preloadedImages.get(src));
                return;
            }

            const img = new Image();
            img.onload = () => {
                this.preloadedImages.set(src, img);
                resolve(img);
            };
            img.onerror = reject;
            img.src = src;
        });
    }

    // Initialize lazy loading for all images on the page
    initializePageImages() {
        // Find all images that should be lazy loaded
        const lazyImages = document.querySelectorAll('img[data-src]');
        lazyImages.forEach(img => this.addLazyImage(img));

        // Convert existing blog images to lazy loading
        const blogImages = document.querySelectorAll('.blog-item img, .post-card img');
        blogImages.forEach(img => {
            if (img.src && !img.dataset.src) {
                img.dataset.src = img.src;
                img.src = '';
                this.addLazyImage(img);
            }
        });
    }

    // Add loading spinner to image containers
    addLoadingSpinner(container) {
        const spinner = document.createElement('div');
        spinner.className = 'image-loading-spinner';
        spinner.innerHTML = `
            <div class="spinner"></div>
            <p>Loading image...</p>
        `;
        container.appendChild(spinner);
        return spinner;
    }

    // Remove loading spinner
    removeLoadingSpinner(container) {
        const spinner = container.querySelector('.image-loading-spinner');
        if (spinner) {
            spinner.remove();
        }
    }
}

// Global instance
window.imageOptimizer = new ImageOptimizer();

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.imageOptimizer.initializePageImages();
});