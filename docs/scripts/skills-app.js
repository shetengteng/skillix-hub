/**
 * Skillix Hub - Vue Skills App Module
 * Handles skills section rendering with Vue.js
 */

(function() {
    'use strict';

    /**
     * Initialize Vue app for skills section
     * This function is called after Vue and skills-data.js are loaded
     */
    function initSkillsApp() {
        // Check if Vue is available
        if (typeof Vue === 'undefined') {
            console.warn('Vue is not loaded, skills app will not be initialized');
            return;
        }
        
        // Check if skills app element exists
        const skillsAppElement = document.getElementById('skills-app');
        if (!skillsAppElement) {
            console.warn('Skills app element not found');
            return;
        }
        
        const { createApp, ref, onMounted } = Vue;
        
        createApp({
            setup() {
                const skills = ref([]);
                const selectedSkill = ref(null);
                
                onMounted(() => {
                    // Load skills from global data
                    if (window.SKILLS_DATA) {
                        skills.value = window.SKILLS_DATA;
                    }
                });
                
                /**
                 * Get SVG path for icon
                 * @param {string} iconName - Icon name
                 * @returns {string} SVG path
                 */
                const getIconPath = (iconName) => {
                    return window.ICON_PATHS ? window.ICON_PATHS[iconName] || window.ICON_PATHS.document : '';
                };
                
                /**
                 * Show skill detail modal
                 * @param {Object} skill - Skill object
                 */
                const showSkillDetail = (skill) => {
                    selectedSkill.value = skill;
                    document.body.style.overflow = 'hidden';
                };
                
                /**
                 * Close skill detail modal
                 */
                const closeModal = () => {
                    selectedSkill.value = null;
                    document.body.style.overflow = '';
                };
                
                // Handle ESC key to close modal
                const handleKeydown = (e) => {
                    if (e.key === 'Escape' && selectedSkill.value) {
                        closeModal();
                    }
                };
                
                // Add keyboard event listener
                document.addEventListener('keydown', handleKeydown);
                
                return {
                    skills,
                    selectedSkill,
                    getIconPath,
                    showSkillDetail,
                    closeModal
                };
            }
        }).mount('#skills-app');
    }
    
    // Export initSkillsApp to global scope for external initialization
    window.initSkillsApp = initSkillsApp;

})();
