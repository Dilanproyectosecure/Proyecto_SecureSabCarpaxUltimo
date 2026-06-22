// landing.js - SecureSab Landing Page

document.addEventListener('DOMContentLoaded', function () {
    // ===== Navbar Scroll Effect =====
    const navbar = document.querySelector('.navbar');
    const scrollThreshold = 50;

    function handleScroll() {
        if (window.scrollY > scrollThreshold) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    }
    window.addEventListener('scroll', handleScroll);
    handleScroll();

    // ===== Mobile Menu Toggle =====
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mobileMenu = document.getElementById('mobileMenu');

    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', function () {
            mobileMenu.classList.toggle('active');
            const icon = mobileMenuBtn.querySelector('i');
            icon.classList.toggle('fa-bars');
            icon.classList.toggle('fa-times');
        });

        mobileMenu.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', function () {
                mobileMenu.classList.remove('active');
                const icon = mobileMenuBtn.querySelector('i');
                icon.classList.add('fa-bars');
                icon.classList.remove('fa-times');
            });
        });
    }

    // ===== Smooth Scroll for Anchor Links =====
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                const navHeight = navbar.offsetHeight;
                const targetPos = target.getBoundingClientRect().top + window.scrollY - navHeight;
                window.scrollTo({ top: targetPos, behavior: 'smooth' });
            }
        });
    });

    // ===== Scroll Reveal Animations =====
    const animateElements = document.querySelectorAll('[data-animate]');

    const observerOptions = {
        threshold: 0.15,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    animateElements.forEach(function (el) {
        observer.observe(el);
    });

    // ===== Hero Stats Counter Animation =====
    function animateCounter(element, target, suffix, duration) {
        var startTime = null;

        function step(timestamp) {
            if (!startTime) startTime = timestamp;
            var progress = Math.min((timestamp - startTime) / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            var current = Math.floor(eased * target);

            if (suffix === '/7') {
                element.textContent = target + '/7';
            } else if (suffix === '%') {
                element.textContent = target + '%';
            } else {
                element.textContent = current + (suffix || '');
            }

            if (progress < 1) {
                requestAnimationFrame(step);
            }
        }
        requestAnimationFrame(step);
    }

    var statsSection = document.querySelector('.card-stats');
    if (statsSection) {
        var statsObserver = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    var numbers = entry.target.querySelectorAll('.stat-number');
                    if (numbers[0]) animateCounter(numbers[0], 5, '', 800);
                    if (numbers[1]) animateCounter(numbers[1], 24, '/7', 800);
                    if (numbers[2]) animateCounter(numbers[2], 100, '%', 800);
                    statsObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });
        statsObserver.observe(statsSection);
    }

    // ===== Stagger Animation for Grid Items =====
    var grids = document.querySelectorAll('.features-grid, .roles-grid');
    grids.forEach(function (grid) {
        var gridObserver = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    var children = entry.target.children;
                    for (var i = 0; i < children.length; i++) {
                        children[i].style.animationDelay = (i * 0.1) + 's';
                        children[i].classList.add('stagger-in');
                    }
                    gridObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });
        gridObserver.observe(grid);
    });
});
