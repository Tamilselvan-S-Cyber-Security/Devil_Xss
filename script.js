// Devil_XSS Website Interactive Features
// Modern JavaScript with ES6+ features

class DevilXSSWebsite {
    constructor() {
        this.init();
        this.setupEventListeners();
        this.startAnimations();
        this.initializeTerminal();
    }

    init() {
        // Smooth scrolling for navigation links
        this.setupSmoothScrolling();
        
        // Initialize scroll animations
        this.setupScrollAnimations();
        
        // Setup mobile navigation
        this.setupMobileNav();
        
        // Initialize payload tabs
        this.setupPayloadTabs();
        
        // Setup copy functionality
        this.setupCopyButtons();
        
        // Initialize typing animation
        this.setupTypingAnimation();
        
        // Setup parallax effects
        this.setupParallaxEffects();
        
        // Initialize tooltips
        this.setupTooltips();
    }

    setupEventListeners() {
        // Window scroll event for navbar
        window.addEventListener('scroll', this.handleScroll.bind(this));
        
        // Window resize event
        window.addEventListener('resize', this.handleResize.bind(this));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboard.bind(this));
        
        // Mouse move for parallax
        document.addEventListener('mousemove', this.handleMouseMove.bind(this));
    }

    // Smooth Scrolling
    setupSmoothScrolling() {
        const navLinks = document.querySelectorAll('.nav-link[href^="#"]');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = link.getAttribute('href');
                const targetElement = document.querySelector(targetId);
                
                if (targetElement) {
                    const offsetTop = targetElement.offsetTop - 70; // Account for fixed navbar
                    window.scrollTo({
                        top: offsetTop,
                        behavior: 'smooth'
                    });
                    
                    // Close mobile menu if open
                    this.closeMobileMenu();
                }
            });
        });
    }

    // Scroll Animations
    setupScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in-up');
                }
            });
        }, observerOptions);

        // Observe elements for animation
        const animateElements = document.querySelectorAll(
            '.xss-type-card, .payload-item, .feature-item, .stat-item, .terminal-window'
        );
        
        animateElements.forEach(el => observer.observe(el));
    }

    // Mobile Navigation
    setupMobileNav() {
        const hamburger = document.querySelector('.hamburger');
        const navMenu = document.querySelector('.nav-menu');
        
        if (hamburger && navMenu) {
            hamburger.addEventListener('click', () => {
                hamburger.classList.toggle('active');
                navMenu.classList.toggle('active');
            });

            // Close menu when clicking on a link
            const navLinks = document.querySelectorAll('.nav-link');
            navLinks.forEach(link => {
                link.addEventListener('click', () => {
                    this.closeMobileMenu();
                });
            });
        }
    }

    closeMobileMenu() {
        const hamburger = document.querySelector('.hamburger');
        const navMenu = document.querySelector('.nav-menu');
        
        if (hamburger && navMenu) {
            hamburger.classList.remove('active');
            navMenu.classList.remove('active');
        }
    }

    // Payload Tabs
    setupPayloadTabs() {
        const tabs = document.querySelectorAll('.payload-tab');
        const contents = document.querySelectorAll('.payload-content');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const targetTab = tab.getAttribute('onclick').match(/'([^']+)'/)[1];
                
                // Remove active class from all tabs and contents
                tabs.forEach(t => t.classList.remove('active'));
                contents.forEach(c => c.classList.remove('active'));
                
                // Add active class to clicked tab and corresponding content
                tab.classList.add('active');
                const targetContent = document.getElementById(`${targetTab}-tab`);
                if (targetContent) {
                    targetContent.classList.add('active');
                }
            });
        });
    }

    // Copy to Clipboard
    setupCopyButtons() {
        const copyButtons = document.querySelectorAll('.copy-btn');
        
        copyButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const payloadItem = e.target.closest('.payload-item');
                const codeElement = payloadItem.querySelector('code');
                const textToCopy = codeElement.textContent;
                
                this.copyToClipboard(textToCopy).then(() => {
                    this.showCopySuccess(button);
                }).catch(() => {
                    this.showCopyError(button);
                });
            });
        });
    }

    async copyToClipboard(text) {
        if (navigator.clipboard && window.isSecureContext) {
            return navigator.clipboard.writeText(text);
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            return new Promise((resolve, reject) => {
                if (document.execCommand('copy')) {
                    resolve();
                } else {
                    reject();
                }
                document.body.removeChild(textArea);
            });
        }
    }

    showCopySuccess(button) {
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        button.classList.add('copied');
        
        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('copied');
        }, 2000);
    }

    showCopyError(button) {
        const originalText = button.textContent;
        button.textContent = 'Error!';
        button.style.background = '#ff4757';
        
        setTimeout(() => {
            button.textContent = originalText;
            button.style.background = '';
        }, 2000);
    }

    // Typing Animation
    setupTypingAnimation() {
        const terminalLines = document.querySelectorAll('.terminal-line');
        let currentLine = 0;
        
        const typeNextLine = () => {
            if (currentLine < terminalLines.length) {
                const line = terminalLines[currentLine];
                const text = line.textContent;
                line.textContent = '';
                line.style.opacity = '1';
                
                this.typeText(line, text, () => {
                    currentLine++;
                    setTimeout(typeNextLine, 500);
                });
            }
        };
        
        // Start typing animation after a delay
        setTimeout(typeNextLine, 1000);
    }

    typeText(element, text, callback) {
        let i = 0;
        const typeInterval = setInterval(() => {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
            } else {
                clearInterval(typeInterval);
                if (callback) callback();
            }
        }, 50);
    }

    // Terminal Animation
    initializeTerminal() {
        const scannerOutput = document.getElementById('scanner-output');
        if (scannerOutput) {
            this.animateScannerOutput(scannerOutput);
        }
    }

    animateScannerOutput(terminal) {
        const lines = [
            '$ python devil_xss.py -f urls.txt -p payloads.txt -o results.txt',
            '[+] Loaded 15 URLs successfully',
            '[+] Loaded 50 XSS payloads successfully',
            '[*] Starting XSS vulnerability scan...',
            '[>] Target [1/15]: https://example.com/search',
            '[💀 VULNERABLE] https://example.com/search?q=<script>alert(\'XSS\')</script>',
            '  ├─ Method: GET | Param: q | Status: 200',
            '  └─ Payload: <script>alert(\'XSS\')</script>',
            '[>] Target [2/15]: https://example.com/contact',
            '[>] Target [3/15]: https://example.com/about',
            '[*] Scanning complete!',
            '[+] Report saved to: results.txt',
            '[i] Total vulnerabilities found: 1'
        ];

        let currentLine = 0;
        const addNextLine = () => {
            if (currentLine < lines.length) {
                const lineDiv = document.createElement('div');
                lineDiv.className = 'terminal-line';
                
                if (lines[currentLine].includes('VULNERABLE')) {
                    lineDiv.innerHTML = `<span class="output vulnerable">${lines[currentLine]}</span>`;
                } else if (lines[currentLine].includes('[+]')) {
                    lineDiv.innerHTML = `<span class="output success">${lines[currentLine]}</span>`;
                } else if (lines[currentLine].includes('[*]')) {
                    lineDiv.innerHTML = `<span class="output info">${lines[currentLine]}</span>`;
                } else if (lines[currentLine].startsWith('$')) {
                    lineDiv.innerHTML = `<span class="prompt">$</span><span class="command">${lines[currentLine].substring(2)}</span>`;
                } else {
                    lineDiv.innerHTML = `<span class="output">${lines[currentLine]}</span>`;
                }
                
                terminal.appendChild(lineDiv);
                terminal.scrollTop = terminal.scrollHeight;
                
                currentLine++;
                setTimeout(addNextLine, Math.random() * 1000 + 500);
            }
        };
        
        // Clear existing content and start animation
        terminal.innerHTML = '';
        setTimeout(addNextLine, 1000);
    }

    // Parallax Effects
    setupParallaxEffects() {
        const hero = document.querySelector('.hero');
        if (hero) {
            this.parallaxElements = hero.querySelectorAll('.hero-content, .hero-animation');
        }
    }

    handleMouseMove(e) {
        if (this.parallaxElements) {
            const mouseX = e.clientX / window.innerWidth;
            const mouseY = e.clientY / window.innerHeight;
            
            this.parallaxElements.forEach((element, index) => {
                const speed = (index + 1) * 0.5;
                const x = (mouseX - 0.5) * speed;
                const y = (mouseY - 0.5) * speed;
                
                element.style.transform = `translate(${x}px, ${y}px)`;
            });
        }
    }

    // Tooltips
    setupTooltips() {
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        
        tooltipElements.forEach(element => {
            element.addEventListener('mouseenter', this.showTooltip.bind(this));
            element.addEventListener('mouseleave', this.hideTooltip.bind(this));
        });
    }

    showTooltip(e) {
        const text = e.target.getAttribute('data-tooltip');
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = text;
        
        document.body.appendChild(tooltip);
        
        const rect = e.target.getBoundingClientRect();
        tooltip.style.left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
        
        setTimeout(() => tooltip.classList.add('show'), 10);
    }

    hideTooltip() {
        const tooltip = document.querySelector('.tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    }

    // Scroll Handlers
    handleScroll() {
        const navbar = document.querySelector('.navbar');
        const scrolled = window.pageYOffset;
        
        if (scrolled > 100) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
        
        // Update active nav link
        this.updateActiveNavLink();
    }

    updateActiveNavLink() {
        const sections = document.querySelectorAll('section[id]');
        const navLinks = document.querySelectorAll('.nav-link');
        
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop - 100;
            if (window.pageYOffset >= sectionTop) {
                current = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    }

    // Keyboard Shortcuts
    handleKeyboard(e) {
        // Ctrl/Cmd + K for search (placeholder)
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            this.focusSearch();
        }
        
        // Escape to close mobile menu
        if (e.key === 'Escape') {
            this.closeMobileMenu();
        }
    }

    focusSearch() {
        // Placeholder for search functionality
        console.log('Search functionality would be implemented here');
    }

    // Resize Handler
    handleResize() {
        // Close mobile menu on resize
        if (window.innerWidth > 768) {
            this.closeMobileMenu();
        }
    }

    // Start Animations
    startAnimations() {
        // Particle animation for hero section
        this.createParticles();
        
        // Glitch effect for title
        this.startGlitchEffect();
    }

    createParticles() {
        const hero = document.querySelector('.hero');
        if (!hero) return;
        
        const particleContainer = document.createElement('div');
        particleContainer.className = 'particles';
        hero.appendChild(particleContainer);
        
        for (let i = 0; i < 50; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 3 + 's';
            particle.style.animationDuration = (Math.random() * 3 + 2) + 's';
            particleContainer.appendChild(particle);
        }
    }

    startGlitchEffect() {
        const glitchElement = document.querySelector('.glitch');
        if (glitchElement) {
            setInterval(() => {
                glitchElement.style.animation = 'none';
                setTimeout(() => {
                    glitchElement.style.animation = 'glitch 2s infinite';
                }, 100);
            }, 5000);
        }
    }
}

// Utility Functions
function scrollToSection(sectionId) {
    const element = document.getElementById(sectionId);
    if (element) {
        const offsetTop = element.offsetTop - 70;
        window.scrollTo({
            top: offsetTop,
            behavior: 'smooth'
        });
    }
}

function showPayloadTab(tabName) {
    const tabs = document.querySelectorAll('.payload-tab');
    const contents = document.querySelectorAll('.payload-content');
    
    tabs.forEach(tab => tab.classList.remove('active'));
    contents.forEach(content => content.classList.remove('active'));
    
    const activeTab = document.querySelector(`[onclick="showPayloadTab('${tabName}')"]`);
    const activeContent = document.getElementById(`${tabName}-tab`);
    
    if (activeTab) activeTab.classList.add('active');
    if (activeContent) activeContent.classList.add('active');
}

function copyToClipboard(element) {
    const payloadItem = element.closest('.payload-item');
    const codeElement = payloadItem.querySelector('code');
    const textToCopy = codeElement.textContent;
    
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(textToCopy).then(() => {
            showCopySuccess(element);
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = textToCopy;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            showCopySuccess(element);
        } catch (err) {
            showCopyError(element);
        }
        
        document.body.removeChild(textArea);
    }
}

function showCopySuccess(button) {
    const originalText = button.textContent;
    button.textContent = 'Copied!';
    button.classList.add('copied');
    
    setTimeout(() => {
        button.textContent = originalText;
        button.classList.remove('copied');
    }, 2000);
}

function showCopyError(button) {
    const originalText = button.textContent;
    button.textContent = 'Error!';
    button.style.background = '#ff4757';
    
    setTimeout(() => {
        button.textContent = originalText;
        button.style.background = '';
    }, 2000);
}

// CSS for particles and additional animations
const additionalCSS = `
.particles {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    overflow: hidden;
}

.particle {
    position: absolute;
    width: 2px;
    height: 2px;
    background: rgba(255, 255, 255, 0.5);
    border-radius: 50%;
    animation: float linear infinite;
}

@keyframes float {
    0% {
        transform: translateY(100vh) rotate(0deg);
        opacity: 0;
    }
    10% {
        opacity: 1;
    }
    90% {
        opacity: 1;
    }
    100% {
        transform: translateY(-100px) rotate(360deg);
        opacity: 0;
    }
}

.navbar.scrolled {
    background: rgba(10, 10, 10, 0.98);
    backdrop-filter: blur(15px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.nav-link.active {
    color: var(--accent-cyan);
}

.nav-link.active::after {
    width: 100%;
}

.tooltip {
    position: absolute;
    background: var(--bg-card);
    color: var(--text-primary);
    padding: var(--spacing-sm) var(--spacing-md);
    border-radius: var(--border-radius);
    font-size: var(--font-size-sm);
    pointer-events: none;
    z-index: 1000;
    opacity: 0;
    transform: translateY(10px);
    transition: all 0.3s ease;
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow-lg);
}

.tooltip.show {
    opacity: 1;
    transform: translateY(0);
}

.tooltip::after {
    content: '';
    position: absolute;
    top: 100%;
    left: 50%;
    margin-left: -5px;
    border-width: 5px;
    border-style: solid;
    border-color: var(--bg-card) transparent transparent transparent;
}

/* Loading Animation */
.loading {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    border-top-color: var(--accent-cyan);
    animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Pulse Animation for Interactive Elements */
.pulse {
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% {
        transform: scale(1);
        box-shadow: 0 0 0 0 rgba(156, 136, 255, 0.7);
    }
    70% {
        transform: scale(1.05);
        box-shadow: 0 0 0 10px rgba(156, 136, 255, 0);
    }
    100% {
        transform: scale(1);
        box-shadow: 0 0 0 0 rgba(156, 136, 255, 0);
    }
}

/* Smooth Transitions for All Interactive Elements */
* {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Custom Scrollbar for Terminal */
.terminal-body {
    scrollbar-width: thin;
    scrollbar-color: var(--accent-purple) var(--bg-tertiary);
}

.terminal-body::-webkit-scrollbar {
    width: 6px;
}

.terminal-body::-webkit-scrollbar-track {
    background: var(--bg-tertiary);
}

.terminal-body::-webkit-scrollbar-thumb {
    background: var(--accent-purple);
    border-radius: 3px;
}

.terminal-body::-webkit-scrollbar-thumb:hover {
    background: var(--accent-blue);
}
`;

// Inject additional CSS
const style = document.createElement('style');
style.textContent = additionalCSS;
document.head.appendChild(style);

// Initialize the website when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DevilXSSWebsite();
});

// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DevilXSSWebsite;
}