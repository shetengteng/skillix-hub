/**
 * Skillix Hub - Language Toggle Module
 * Handles Chinese/English language switching
 */

(function() {
    'use strict';

    const langToggle = document.getElementById('langToggle');
    const html = document.documentElement;
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

})();
