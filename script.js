// ===== HIRING BANNER =====
const hiringBanner = document.getElementById('hiring-banner');
const dismissBtn = document.getElementById('dismiss-banner');
const navbarEl = document.getElementById('navbar');

function updateNavbarOffset() {
    if (hiringBanner && navbarEl) {
        const bannerH = hiringBanner.offsetHeight;
        navbarEl.style.top = bannerH + 'px';
    }
}

if (hiringBanner && dismissBtn) {
    // Check if previously dismissed this session
    if (sessionStorage.getItem('bannerDismissed')) {
        hiringBanner.style.display = 'none';
        if (navbarEl) navbarEl.style.top = '0px';
    } else {
        updateNavbarOffset();
        window.addEventListener('resize', updateNavbarOffset);
    }

    dismissBtn.addEventListener('click', () => {
        hiringBanner.style.maxHeight = hiringBanner.offsetHeight + 'px';
        hiringBanner.offsetHeight; // force reflow
        hiringBanner.style.maxHeight = '0';
        hiringBanner.style.paddingTop = '0';
        hiringBanner.style.paddingBottom = '0';
        hiringBanner.style.overflow = 'hidden';
        if (navbarEl) navbarEl.style.transition = 'top 0.3s ease';
        if (navbarEl) navbarEl.style.top = '0px';
        sessionStorage.setItem('bannerDismissed', 'true');
        setTimeout(() => { hiringBanner.style.display = 'none'; }, 300);
    });
}

// ===== SCROLL REVEAL =====
const revealElements = document.querySelectorAll('.reveal-up');
const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
            setTimeout(() => entry.target.classList.add('revealed'), i * 80);
            revealObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
revealElements.forEach(el => revealObserver.observe(el));

// ===== FAQ ACCORDION (Enhanced for Dynamic Content) =====
const faqContainer = document.getElementById('faq-accordion-container');
if (faqContainer) {
    faqContainer.addEventListener('click', (e) => {
        const btn = e.target.closest('.faq-btn');
        if (!btn) return;

        const item = btn.parentElement;
        const content = item.querySelector('.faq-content');
        const icon = item.querySelector('.faq-icon');
        const isOpen = content.style.maxHeight && content.style.maxHeight !== '0px';

        // Close others in the same container
        faqContainer.querySelectorAll('.faq-content').forEach(c => c.style.maxHeight = '0px');
        faqContainer.querySelectorAll('.faq-icon').forEach(i => i.classList.remove('active'));

        if (!isOpen) {
            content.style.maxHeight = content.scrollHeight + 'px';
            icon.classList.add('active');
        }
    });
}

// ===== NAVBAR SCROLL =====
window.addEventListener('scroll', () => {
    navbarEl.classList.toggle('scrolled', window.scrollY > 50);
});

// ===== MOBILE MENU =====
const mobileBtn = document.getElementById('mobile-menu-btn');
const mobileMenu = document.getElementById('mobile-menu');
mobileBtn.addEventListener('click', () => {
    mobileMenu.classList.toggle('hidden');
});
document.querySelectorAll('.mobile-nav-link').forEach(link => {
    link.addEventListener('click', () => mobileMenu.classList.add('hidden'));
});

// ===== ACTIVE NAV LINK =====
const sections = document.querySelectorAll('section[id]');
window.addEventListener('scroll', () => {
    sections.forEach(section => {
        const rect = section.getBoundingClientRect();
        const id = section.getAttribute('id');
        const link = document.querySelector(`.nav-link[href="#${id}"]`);
        if (link) {
            link.classList.toggle('active', rect.top <= 150 && rect.bottom > 150);
        }
    });
});

// ===== COUNTER ANIMATION =====
const counters = document.querySelectorAll('.counter');
const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        const el = entry.target;
        if (entry.isIntersecting) {
            // State lock: Do not restart if already running!
            if (el.dataset.running) return;
            el.dataset.running = "true";
            
            const target = parseInt(el.dataset.target);
            const duration = 2000;
            let start = null; // Sync time IN the frame
            
            const animate = (timestamp) => {
                if (!start) start = timestamp;
                const progress = Math.min((timestamp - start) / duration, 1);
                const eased = 1 - Math.pow(1 - progress, 3);
                
                if (progress < 1) {
                    el.textContent = Math.round(eased * target);
                    el.animationID = requestAnimationFrame(animate);
                } else {
                    el.textContent = target;
                }
            };
            cancelAnimationFrame(el.animationID);
            el.animationID = requestAnimationFrame(animate);
        } else {
            // Stop and reset when scrolled out of view completely
            cancelAnimationFrame(el.animationID);
            el.textContent = "0";
            el.dataset.running = "";
        }
    });
}, { threshold: 0.1 }); // Lower threshold to beat the CSS zoom bug
counters.forEach(c => counterObserver.observe(c));

// // ===== DYNAMIC PROJECTS GALLERY =====
// (async () => {
//     try {
//         const res = await fetch('projects.json');
//         const projects = await res.json();
//         const grid = document.getElementById('project-gallery-grid');
        
//         if (grid) {
//             projects.forEach((p, index) => {
//                 const card = document.createElement('a');
//                 card.href = `project.html?id=${p.id}`;
//                 // Adding custom delay for staggered fade-up animation
//                 card.className = 'gallery-item block group relative overflow-hidden rounded-md cursor-pointer opacity-0 translate-y-8';
//                 card.style.animation = `fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) ${index * 0.1}s forwards`;
                
//                 // For a 6-item grid, make the 2nd item larger to replicate the old masonry-like feel
//                 if (index === 1) card.classList.add('lg:col-span-2', 'lg:row-span-2');

//                 card.innerHTML = `
//                     <img src="${p.cover}" alt="${p.name}" class="w-full ${index === 1 ? 'h-72 lg:h-full' : 'h-72'} object-cover group-hover:scale-110 transition-transform duration-700">
//                     <div class="absolute inset-0 bg-gradient-to-t from-primary/90 via-primary/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 flex items-end p-6">
//                         <div>
//                             <h4 class="font-manrope font-700 text-white text-lg translate-y-4 group-hover:translate-y-0 transition-transform duration-500">${p.name}</h4>
//                             <p class="text-primary-fixed-dim text-xs tracking-wider uppercase opacity-0 group-hover:opacity-100 transition-opacity duration-500 delay-100">${p.category}</p>
//                             <p class="text-tertiary-fixed-dim text-xs mt-1 opacity-0 group-hover:opacity-100 transition-opacity duration-500 delay-150">📍 ${p.location}</p>
//                         </div>
//                     </div>
//                 `;
//                 grid.appendChild(card);
//             });
//         }
//     } catch (e) {
//         console.warn('Projects data unavailable:', e);
//     }
// })();
// // ===== DYNAMIC EXPANDING PROJECTS GALLERY =====
// (async () => {
//     try {
//         const res = await fetch('projects.json');
//         const projects = await res.json();
//         const grid = document.getElementById('project-gallery-grid');

//         if (grid) {
//             // Display all projects for the expanding layout
//             projects.forEach((p, index) => {
//                 const card = document.createElement('a');
//                 card.href = `project.html?id=${p.id}`;
//                 card.className = 'relative group flex-grow transition-all w-56 h-[400px] shrink-0 md:shrink duration-500 hover:w-full opacity-0 translate-y-8 overflow-hidden rounded-md';
//                 card.style.animation = `fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) ${index * 0.1}s forwards`;
                
//                 card.innerHTML = `
//                     <img src="${p.cover}" alt="${p.name}" class="h-full w-full object-cover object-center transition-transform duration-700 group-hover:scale-105">
//                     <div class="absolute inset-0 flex flex-col justify-end p-10 text-white bg-gradient-to-t from-primary/90 via-primary/50 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-500">
//                         <h3 class="font-manrope font-700 text-2xl mb-2">${p.name}</h3>
//                         <p class="text-primary-fixed-dim text-xs tracking-wider uppercase mb-1">${p.category}</p>
//                         <p class="text-tertiary-fixed-dim text-sm">📍 ${p.location}</p>
//                     </div>
//                 `;
                
//                 grid.appendChild(card);
//             });
//         }
//     } catch (e) {
//         console.warn('Projects data unavailable:', e);
//     }
// })();

// ============================================
// EXPANDING GALLERY WITH LAZY LOADING
// ============================================

(function() {
    'use strict';

    const CONFIG = {
        jsonPath: 'projects.json',
        observerRootMargin: '150px',
        observerThreshold: 0.1,
        preloadCount: 3,
        animationDelay: 0.08,
        maxIndicators: 6
    };

    const grid = document.getElementById('project-gallery-grid');
    const indicatorsContainer = document.getElementById('gallery-scroll-indicators');

    if (!grid) return;

    let projects = [];
    let loadedImages = new Set();

    // ============================================
    // INTERSECTION OBSERVER FOR LAZY LOADING
    // ============================================
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const card = entry.target;
                const img = card.querySelector('.gallery-image');
                
                if (img && !loadedImages.has(img)) {
                    loadImage(img);
                    loadedImages.add(img);
                }
                
                observer.unobserve(card);
            }
        });
    }, {
        rootMargin: CONFIG.observerRootMargin,
        threshold: CONFIG.observerThreshold
    });

    // ============================================
    // LOAD IMAGE WITH BLUR-UP EFFECT
    // ============================================
    function loadImage(img) {
        const src = img.dataset.src;
        if (!src) return;

        const preloadImg = new Image();
        
        preloadImg.onload = () => {
            img.src = src;
            img.classList.add('loaded');
            
            const placeholder = img.parentElement.querySelector('.gallery-blur-placeholder');
            if (placeholder) {
                setTimeout(() => {
                    placeholder.classList.add('fade-out');
                }, 100);
            }
        };

        preloadImg.onerror = () => {
            console.warn(`Failed to load: ${src}`);
            const originalSrc = img.dataset.fallback;
            if (originalSrc && originalSrc !== src) {
                img.src = originalSrc;
                img.classList.add('loaded');
            }
        };

        preloadImg.src = src;
    }

    // ============================================
    // CREATE GALLERY CARD WITH EXPANDING EFFECT
    // ============================================
    function createGalleryCard(project, index) {
        const card = document.createElement('a');
        card.href = `project.html?id=${project.id}`;
        card.className = 'gallery-card group';
        card.style.animationDelay = `${index * CONFIG.animationDelay}s`;
        card.setAttribute('role', 'listitem');
        card.setAttribute('aria-label', `View project: ${project.name}`);
        card.setAttribute('tabindex', '0');

        const thumbnailSrc = project.thumbnail || project.coverOptimized || project.cover;
        const blurSrc = project.blurDataUrl || '';
        const dominantColor = project.dominantColor || '#e5e7eb';
        const fallbackSrc = project.cover;

        // Get media count for extra info
        const mediaCount = project.media ? project.media.length : 0;

        card.innerHTML = `
            <div class="gallery-image-container" style="background-color: ${dominantColor}">
                <!-- Blur Placeholder -->
                ${blurSrc ? `
                    <img 
                        src="${blurSrc}" 
                        alt="" 
                        class="gallery-blur-placeholder"
                        aria-hidden="true"
                        draggable="false"
                    >
                ` : `
                    <div 
                        class="gallery-blur-placeholder" 
                        style="background-color: ${dominantColor}"
                        aria-hidden="true"
                    ></div>
                `}
                
                <!-- Main Image -->
                <img 
                    src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
                    data-src="${thumbnailSrc}"
                    data-fallback="${fallbackSrc}"
                    alt="${project.name}"
                    class="gallery-image"
                    loading="lazy"
                    decoding="async"
                    draggable="false"
                >
            </div>
            
            <!-- Overlay -->
            <div class="gallery-overlay">
                <p class="gallery-category">${project.category || 'Project'}</p>
                <h3 class="font-manrope">${project.name}</h3>
                <p class="gallery-location">
                    <svg fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"/>
                    </svg>
                    ${project.location || 'Location'}
                </p>
                
                <!-- Extra info shown on expand -->
                <div class="gallery-extra-info">
                    <div class="flex items-center gap-4 text-xs text-white/70 mt-2">
                        ${mediaCount > 0 ? `
                            <span class="flex items-center gap-1">
                                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                                </svg>
                                ${mediaCount} Photos
                            </span>
                        ` : ''}
                        <span class="flex items-center gap-1">
                            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                            </svg>
                            View Details
                        </span>
                    </div>
                </div>
            </div>
        `;

        // Keyboard navigation
        card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                card.click();
            }
        });

        return card;
    }

    // ============================================
    // PRELOAD FIRST FEW IMAGES
    // ============================================
    function preloadInitialImages(cards) {
        const count = Math.min(CONFIG.preloadCount, cards.length);
        
        for (let i = 0; i < count; i++) {
            const img = cards[i].querySelector('.gallery-image');
            if (img && !loadedImages.has(img)) {
                loadImage(img);
                loadedImages.add(img);
            }
        }
    }

    // ============================================
    // SCROLL INDICATORS (Mobile)
    // ============================================
    function initScrollIndicators(projectCount) {
        if (!indicatorsContainer || projectCount <= 1) return;

        const indicatorCount = Math.min(projectCount, CONFIG.maxIndicators);

        for (let i = 0; i < indicatorCount; i++) {
            const dot = document.createElement('div');
            dot.className = `scroll-indicator ${i === 0 ? 'active' : ''}`;
            indicatorsContainer.appendChild(dot);
        }

        let scrollTimeout;
        grid.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                const scrollPercent = grid.scrollLeft / (grid.scrollWidth - grid.clientWidth);
                const activeIndex = Math.min(
                    Math.round(scrollPercent * (indicatorCount - 1)),
                    indicatorCount - 1
                );

                indicatorsContainer.querySelectorAll('.scroll-indicator').forEach((dot, i) => {
                    dot.classList.toggle('active', i === activeIndex);
                });
            }, 50);
        }, { passive: true });
    }

    // ============================================
    // KEYBOARD NAVIGATION
    // ============================================
    function initKeyboardNavigation() {
        grid.addEventListener('keydown', (e) => {
            const focusedCard = document.activeElement;
            
            if (!focusedCard?.classList.contains('gallery-card')) return;

            if (e.key === 'ArrowRight') {
                e.preventDefault();
                const next = focusedCard.nextElementSibling;
                if (next?.classList.contains('gallery-card')) {
                    next.focus();
                    next.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
                }
            } else if (e.key === 'ArrowLeft') {
                e.preventDefault();
                const prev = focusedCard.previousElementSibling;
                if (prev?.classList.contains('gallery-card')) {
                    prev.focus();
                    prev.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
                }
            }
        });
    }

    // ============================================
    // SHOW ERROR STATE
    // ============================================
    function showError(message = 'Unable to load projects') {
        const skeleton = grid.querySelector('.skeleton-loader');
        if (skeleton) skeleton.remove();

        grid.innerHTML = `
            <div class="gallery-error">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" 
                          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
                <p>${message}</p>
                <button onclick="location.reload()">Try Again</button>
            </div>
        `;
    }

    // ============================================
    // REMOVE SKELETON LOADER
    // ============================================
    function removeSkeleton() {
        const skeleton = grid.querySelector('.skeleton-loader');
        if (skeleton) {
            skeleton.classList.add('fade-out');
            setTimeout(() => skeleton.remove(), 300);
        }
    }

    // ============================================
    // MAIN INITIALIZATION
    // ============================================
    async function initGallery() {
        try {
            const response = await fetch(CONFIG.jsonPath);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            projects = await response.json();

            if (!Array.isArray(projects) || projects.length === 0) {
                throw new Error('No projects found');
            }

            // Remove skeleton
            removeSkeleton();

            // Create cards
            const cards = [];
            projects.forEach((project, index) => {
                const card = createGalleryCard(project, index);
                grid.appendChild(card);
                cards.push(card);
            });

            // Setup lazy loading
            cards.forEach((card, index) => {
                if (index >= CONFIG.preloadCount) {
                    imageObserver.observe(card);
                }
            });

            // Preload first images
            preloadInitialImages(cards);

            // Init scroll indicators
            initScrollIndicators(projects.length);

            // Init keyboard navigation
            initKeyboardNavigation();

            console.log(`✓ Gallery loaded: ${projects.length} projects`);

        } catch (error) {
            console.error('Gallery initialization failed:', error);
            showError('Unable to load projects. Please try again.');
        }
    }

    // Start
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initGallery);
    } else {
        initGallery();
    }

})();

// ===== CONTACT FORM =====
document.getElementById('contact-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.textContent = 'Sending...';
    btn.disabled = true;
    setTimeout(() => {
        e.target.reset();
        btn.innerHTML = 'Send Message <span class="material-icons-outlined text-lg">send</span>';
        btn.disabled = false;
        document.getElementById('form-success').classList.remove('hidden');
        setTimeout(() => document.getElementById('form-success').classList.add('hidden'), 4000);
    }, 1500);
});

// ===== SCROLL PROGRESS BAR =====
const progressBar = document.createElement('div');
progressBar.id = 'scroll-progress';
document.body.prepend(progressBar);
window.addEventListener('scroll', () => {
    const scrollTop = window.scrollY;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    progressBar.style.width = (scrollTop / docHeight * 100) + '%';
});

// ===== SMOOTH SCROLL FOR ANCHOR LINKS =====
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
        e.preventDefault();
        const target = document.querySelector(anchor.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// ===== DYNAMIC TEAM LOADING =====
(async () => {
    try {
        const res = await fetch('team.json');
        const members = await res.json();
        const grid = document.getElementById('team-grid');
        const joinCard = grid.querySelector('.group'); // the Join Team card

        members.forEach(m => {
            const card = document.createElement('div');
            card.className = 'reveal-up team-card-container';
            card.innerHTML = `
                <div class="team-card-inner">
                    <!-- Front Face -->
                    <div class="team-card-front">
                        <div class="relative overflow-hidden rounded-md mb-5">
                            <img src="${m.image}" alt="${m.name}" class="w-full h-48 sm:h-64 lg:h-72 object-cover object-top transition-transform duration-700">
                        </div>
                        <h3 class="font-manrope font-700 text-lg text-white">${m.name}</h3>
                        <p class="text-gray-400 text-sm">${m.role}</p>
                    </div>
                    <!-- Back Face (About + Socials) -->
                    <div class="team-card-back">
                        <div class="mb-4">
                            <span class="material-icons-outlined text-tertiary-fixed-dim text-4xl">contact_support</span>
                        </div>
                        <h3 class="font-manrope font-700 text-lg text-white mb-2">${m.name}</h3>
                        <p class="text-primary-fixed-dim text-sm leading-relaxed mb-6">${m.about}</p>
                        <div class="flex gap-3">
                            <a href="${m.linkedin}" target="_blank" rel="noopener noreferrer" class="w-9 h-9 rounded-full bg-white/20 backdrop-blur flex items-center justify-center text-white hover:bg-tertiary-fixed-dim hover:text-primary transition-all">
                                <span class="text-xs font-700">in</span>
                            </a>
                            ${m.email ? `
                            <a href="mailto:${m.email}" class="w-9 h-9 rounded-full bg-white/20 backdrop-blur flex items-center justify-center text-white hover:bg-tertiary-fixed-dim hover:text-primary transition-all">
                                <span class="material-icons-outlined text-sm">email</span>
                            </a>` : ''}
                        </div>
                    </div>
                </div>
            `;
            grid.insertBefore(card, joinCard);
        });

        // Re-observe new elements for scroll reveal
        grid.querySelectorAll('.reveal-up:not(.revealed)').forEach(el => revealObserver.observe(el));
    } catch (e) {
        console.warn('Team data unavailable:', e);
    }
})();

// ===== DYNAMIC REVIEWS =====
(async () => {
    try {
        const res = await fetch('reviews.json');
        const reviews = await res.json();
        const container = document.getElementById('reviews-container');
        const countEl = document.getElementById('review-count');

        if (countEl) {
            countEl.textContent = `${reviews.length} Client Reviews`;
        }

        // Calculate aggregate score
        const avgRating = (reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length).toFixed(1);
        const aggEl = document.querySelector('#testimonials .font-700.text-2xl');
        if (aggEl) aggEl.textContent = avgRating;

        reviews.forEach(r => {
            const stars = Array.from({ length: 5 }, (_, i) =>
                `<span class="${i < r.rating ? 'text-tertiary-fixed-dim' : 'text-outline'}">\u2605</span>`
            ).join('');

            const card = document.createElement('div');
            card.className = 'testimonial-card bg-primary-container/60 backdrop-blur-md p-8 rounded-md';
            card.innerHTML = `
                <div class="flex gap-1 mb-4">${stars}</div>
                <p class="text-primary-fixed-dim leading-relaxed mb-6 italic">"${r.review}"</p>
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full bg-tertiary-fixed-dim flex items-center justify-center font-manrope font-700 text-primary text-sm">${r.initials}</div>
                    <div>
                        <p class="text-white font-manrope font-600 text-sm">${r.name}</p>
                        <p class="text-primary-fixed-dim text-xs">${r.role}</p>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });

        // Scroll controls + Autoscroll
        const scrollLeftBtn = document.getElementById('scroll-left');
        const scrollRightBtn = document.getElementById('scroll-right');
        const scrollAmount = 370;
        let autoScrollInterval = null;
        let pauseTimeout = null;

        function startAutoScroll() {
            stopAutoScroll();
            autoScrollInterval = setInterval(() => {
                // If at the end, loop back to start
                if (container.scrollLeft + container.clientWidth >= container.scrollWidth - 10) {
                    container.scrollTo({ left: 0, behavior: 'smooth' });
                } else {
                    container.scrollBy({ left: scrollAmount, behavior: 'smooth' });
                }
            }, 1800);
        }

        function stopAutoScroll() {
            if (autoScrollInterval) {
                clearInterval(autoScrollInterval);
                autoScrollInterval = null;
            }
        }

        function pauseAndResume() {
            stopAutoScroll();
            clearTimeout(pauseTimeout);
            pauseTimeout = setTimeout(startAutoScroll, 5000);
        }

        // Arrow buttons
        scrollLeftBtn?.addEventListener('click', () => {
            container.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
            pauseAndResume();
        });
        scrollRightBtn?.addEventListener('click', () => {
            container.scrollBy({ left: scrollAmount, behavior: 'smooth' });
            pauseAndResume();
        });

        // Pause on hover
        container.addEventListener('mouseenter', stopAutoScroll);
        container.addEventListener('mouseleave', startAutoScroll);

        // Pause on touch (mobile)
        container.addEventListener('touchstart', () => { stopAutoScroll(); clearTimeout(pauseTimeout); });
        container.addEventListener('touchend', () => { pauseTimeout = setTimeout(startAutoScroll, 5000); });

        // Start autoscroll
        startAutoScroll();
    } catch (err) {
        console.error('Failed to load reviews:', err);
    }
})();

// ===== DYNAMIC FAQ LOADING =====
(async () => {
    const container = document.getElementById('faq-accordion-container');
    if (!container) return;

    try {
        const res = await fetch('faq.json');
        const faqs = await res.json();
        
        // Clear skeleton/loader
        container.innerHTML = '';

        faqs.forEach(f => {
            const item = document.createElement('div');
            item.className = 'faq-item reveal-up bg-white rounded-md border border-gray-200 overflow-hidden';
            if (f.delay) item.style.animationDelay = f.delay;
            
            item.innerHTML = `
                <button class="faq-btn w-full px-8 py-6 text-left flex justify-between items-center group focus:outline-none">
                    <span class="font-manrope font-700 text-lg text-primary group-hover:text-tertiary-fixed-dim transition-colors">${f.question}</span>
                    <span class="material-icons-outlined text-tertiary-fixed-dim transition-transform duration-300 faq-icon">expand_more</span>
                </button>
                <div class="faq-content max-h-0 overflow-hidden transition-all duration-500 ease-in-out">
                    <div class="px-8 pb-8 text-on-surface-variant leading-relaxed">
                        ${f.answer}
                    </div>
                </div>
            `;
            container.appendChild(item);
        });

        // Re-observe new FAQ items for reveal effect
        container.querySelectorAll('.reveal-up').forEach(el => revealObserver.observe(el));

    } catch (e) {
        console.warn('FAQ data unavailable:', e);
        container.innerHTML = '<p class="text-center py-10 text-gray-500">Frequently asked questions are currently unavailable. Please check back later.</p>';
    }
})();

// ===== HANDLE EXTERNAL HASH LINKS ON LOAD =====
window.addEventListener('load', () => {
    if (window.location.hash) {
        setTimeout(() => {
            const target = document.querySelector(window.location.hash);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }, 400); // Give JS time to fetch and render reviews/team 
    }
});
