// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Scroll to chat function
function scrollToChat() {
    const chatSection = document.getElementById('chat');
    if (chatSection) {
        chatSection.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Add animation on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe all feature cards and command items
document.querySelectorAll('.feature-card, .command-item, .tech-item').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
});

// Copy to clipboard for command items
document.querySelectorAll('.command-item code').forEach(code => {
    code.addEventListener('click', function() {
        const text = this.textContent;
        navigator.clipboard.writeText(text).then(() => {
            // Show feedback
            const originalText = this.textContent;
            this.textContent = '✓ Copied!';
            setTimeout(() => {
                this.textContent = originalText;
            }, 2000);
        });
    });
});

// Add active state to nav menu based on scroll position
window.addEventListener('scroll', () => {
    let current = '';
    
    document.querySelectorAll('section').forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.clientHeight;
        if (pageYOffset >= sectionTop - 200) {
            current = section.getAttribute('id');
        }
    });

    document.querySelectorAll('.nav-menu a').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === '#' + current) {
            link.classList.add('active');
        }
    });
});

// Particle background effect
function createParticles() {
    const hero = document.querySelector('.hero');
    if (!hero) return;
    
    // Create subtle particle effect using CSS
    // This is handled by existing gradients for performance
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    createParticles();
    
    // Add loading animation
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.transition = 'opacity 0.5s ease';
        document.body.style.opacity = '1';
    }, 100);
});

// Mobile menu toggle (if needed in future)
const navMenu = document.querySelector('.nav-menu');
const navLogo = document.querySelector('.nav-logo');

// Add some interactivity to player cards
document.querySelectorAll('.player-card').forEach((card, index) => {
    card.addEventListener('mouseenter', () => {
        card.style.animation = 'float 3s ease-in-out infinite';
    });
});

// Keyboard navigation
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        // Close any dropdowns or modals if needed in future
    }
});
