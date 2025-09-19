// animations.js - For handling animations on the pages

document.addEventListener('DOMContentLoaded', function() {
    // Animate stats numbers if they exist
    const animateStats = () => {
        const statElements = document.querySelectorAll('.stat-number');
        if (statElements.length === 0) return;
        
        statElements.forEach(stat => {
            const targetValue = parseInt(stat.getAttribute('data-value') || '0');
            const duration = 2000; // 2 seconds
            const startTime = Date.now();
            const startValue = 0;
            
            const updateValue = () => {
                const currentTime = Date.now();
                const elapsed = currentTime - startTime;
                
                if (elapsed < duration) {
                    const value = Math.floor(startValue + (targetValue - startValue) * (elapsed / duration));
                    stat.textContent = value.toLocaleString();
                    requestAnimationFrame(updateValue);
                } else {
                    stat.textContent = targetValue.toLocaleString();
                }
            };
            
            updateValue();
        });
    };
    
    // Check if element is in viewport
    const isInViewport = (element) => {
        const rect = element.getBoundingClientRect();
        return (
            rect.top <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.bottom >= 0
        );
    };
    
    // Add animations when elements come into view
    const handleScrollAnimations = () => {
        const elements = document.querySelectorAll('.animate-on-scroll');
        elements.forEach(element => {
            if (isInViewport(element) && !element.classList.contains('animate-fadeInUp')) {
                element.classList.add('animate-fadeInUp');
                
                // If this is a stats section, animate the numbers
                if (element.classList.contains('stats-section')) {
                    animateStats();
                }
            }
        });
    };
    
    // Initial check for animations
    handleScrollAnimations();
    
    // Listen for scroll events
    window.addEventListener('scroll', handleScrollAnimations);
    
    // Handle map interactions if map exists
    const mapElement = document.getElementById('map');
    if (mapElement) {
        const zoomInBtn = document.getElementById('zoom-in');
        const zoomOutBtn = document.getElementById('zoom-out');
        
        if (zoomInBtn && map) {
            zoomInBtn.addEventListener('click', () => {
                map.zoomIn();
            });
        }
        
        if (zoomOutBtn && map) {
            zoomOutBtn.addEventListener('click', () => {
                map.zoomOut();
            });
        }
        
        // Add active class to filter buttons when clicked
        const filterBtns = document.querySelectorAll('.filter-btn');
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const isActive = btn.classList.contains('active');
                
                // If this is a multi-select filter
                if (btn.closest('.filter-group').classList.contains('multi-select')) {
                    if (isActive) {
                        btn.classList.remove('active');
                    } else {
                        btn.classList.add('active');
                    }
                } else {
                    // Single select filter - deactivate others
                    btn.closest('.filter-group').querySelectorAll('.filter-btn').forEach(b => {
                        b.classList.remove('active');
                    });
                    btn.classList.add('active');
                }
            });
        });
    }
});
