// clickable-cards.js - Makes blog cards clickable
class ClickableCards {
    constructor() {
        this.init();
    }

    init() {
        // Add click handlers to all clickable cards
        document.addEventListener('click', (e) => {
            const card = e.target.closest('.clickable-card');
            if (card) {
                // Don't trigger if clicking on a tag
                if (!e.target.classList.contains('tag') && !e.target.classList.contains('tag-filter')) {
                    this.handleCardClick(card);
                }
            }
        });

        // Add hover effects
        this.addHoverEffects();
    }

    handleCardClick(card) {
        const url = card.dataset.url;
        if (url) {
            // Add a subtle click animation
            card.style.transform = 'scale(0.98)';
            setTimeout(() => {
                window.location.href = url;
            }, 100);
        }
    }

    addHoverEffects() {
        const cards = document.querySelectorAll('.clickable-card');
        cards.forEach(card => {
            // Add cursor pointer
            card.style.cursor = 'pointer';
            
            // Add hover effect
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-8px) rotate(1deg)';
                card.style.transition = 'all 0.3s ease';
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0) rotate(0deg)';
            });
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ClickableCards();
});