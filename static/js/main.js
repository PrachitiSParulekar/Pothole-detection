// main.js - CivicSightAI Modern Theme

// Intersection Observer for scroll animations
document.addEventListener('DOMContentLoaded', function() {
    // Observer for fade-in animations
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };
    
    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fadeInUp');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Target elements to animate
    const animateElements = document.querySelectorAll('.animate-on-scroll');
    animateElements.forEach(el => {
        observer.observe(el);
    });
    
    // Upload form functionality
    const dropzone = document.getElementById('upload-dropzone');
    const fileInput = document.getElementById('file-input');
    
    if (dropzone && fileInput) {
        // Handle click on dropzone
        dropzone.addEventListener('click', () => {
            fileInput.click();
        });
        
        // Handle drag and drop
        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('active');
        });
        
        dropzone.addEventListener('dragleave', () => {
            dropzone.classList.remove('active');
        });
        
        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('active');
            
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                updateFilePreview(e.dataTransfer.files[0]);
            }
        });
        
        // Update preview when file selected
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) {
                updateFilePreview(fileInput.files[0]);
            }
        });
        
        function updateFilePreview(file) {
            const previewElement = document.getElementById('file-preview');
            if (!previewElement) return;
            
            // Clear previous preview
            previewElement.innerHTML = '';
            
            // Check if file is an image
            if (file.type.startsWith('image/')) {
                const img = document.createElement('img');
                img.classList.add('preview-image');
                img.file = file;
                
                previewElement.appendChild(img);
                
                const reader = new FileReader();
                reader.onload = (e) => { img.src = e.target.result; };
                reader.readAsDataURL(file);
                
                // Update dropzone text
                const dropzoneText = document.querySelector('.dropzone-text');
                if (dropzoneText) {
                    dropzoneText.textContent = file.name;
                }
            }
        }
    }
    
    // Flash message auto-dismiss
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });
    
    // Mobile menu toggle
    const menuToggle = document.getElementById('menu-toggle');
    const navMenu = document.getElementById('nav-menu');
    
    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', () => {
            navMenu.classList.toggle('show');
            menuToggle.classList.toggle('active');
        });
    }
    
    // Dark/Light mode toggle (if implemented)
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('light-mode');
            
            // Store preference
            const isDarkMode = document.body.classList.contains('light-mode') ? 'light' : 'dark';
            localStorage.setItem('theme-preference', isDarkMode);
        });
        
        // Check for saved preference
        const savedTheme = localStorage.getItem('theme-preference');
        if (savedTheme === 'light') {
            document.body.classList.add('light-mode');
        }
    }
});

// Stats Counter Animation
function animateCounters() {
    const counters = document.querySelectorAll('.stat-counter');
    
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-target'));
        const duration = 2000; // ms
        const step = target / (duration / 16); // 16ms is roughly 60fps
        let current = 0;
        
        const updateCounter = () => {
            current += step;
            if (current < target) {
                counter.textContent = Math.floor(current);
                requestAnimationFrame(updateCounter);
            } else {
                counter.textContent = target;
            }
        };
        
        updateCounter();
    });
}

// Initialize map if needed
function initMap() {
    const mapElement = document.getElementById('heatmap');
    if (mapElement && window.mapData) {
        // Map initialization code here if using a mapping library
        console.log("Map initialization would happen here");
    }
}

// Call init map when DOM is loaded
document.addEventListener('DOMContentLoaded', initMap);
