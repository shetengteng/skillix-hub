/**
 * Skillix Hub - JavaScript
 * Theme toggle and language toggle functionality
 */

(function() {
    'use strict';

    // ==========================================================================
    // Theme Toggle
    // ==========================================================================
    
    const themeToggle = document.getElementById('themeToggle');
    const html = document.documentElement;
    
    /**
     * Initialize theme based on saved preference or system preference
     */
    function initTheme() {
        const savedTheme = localStorage.getItem('theme');
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
            html.classList.add('dark');
        } else {
            html.classList.remove('dark');
        }
    }
    
    /**
     * Toggle between light and dark theme
     */
    function toggleTheme() {
        html.classList.toggle('dark');
        const isDark = html.classList.contains('dark');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    }
    
    // Initialize theme on page load
    initTheme();
    
    // Add click event listener
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
            if (e.matches) {
                html.classList.add('dark');
            } else {
                html.classList.remove('dark');
            }
        }
    });

    // ==========================================================================
    // Language Toggle
    // ==========================================================================
    
    const langToggle = document.getElementById('langToggle');
    const body = document.body;
    
    /**
     * Initialize language based on saved preference
     */
    function initLanguage() {
        const savedLang = localStorage.getItem('lang');
        
        if (savedLang === 'en') {
            body.setAttribute('data-lang', 'en');
            html.setAttribute('lang', 'en');
        } else {
            body.removeAttribute('data-lang');
            html.setAttribute('lang', 'zh-CN');
        }
    }
    
    /**
     * Toggle between Chinese and English
     */
    function toggleLanguage() {
        const currentLang = body.getAttribute('data-lang');
        
        if (currentLang === 'en') {
            body.removeAttribute('data-lang');
            html.setAttribute('lang', 'zh-CN');
            localStorage.setItem('lang', 'zh');
        } else {
            body.setAttribute('data-lang', 'en');
            html.setAttribute('lang', 'en');
            localStorage.setItem('lang', 'en');
        }
    }
    
    // Initialize language on page load
    initLanguage();
    
    // Add click event listener
    if (langToggle) {
        langToggle.addEventListener('click', toggleLanguage);
    }

    // ==========================================================================
    // Smooth Scroll for Anchor Links
    // ==========================================================================
    
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            
            if (href === '#') return;
            
            e.preventDefault();
            
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

})();
