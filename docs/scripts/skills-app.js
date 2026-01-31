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
                const activeUseCaseIndex = ref(0);
                
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
                    activeUseCaseIndex.value = 0; // Reset to first use case
                    document.body.style.overflow = 'hidden';
                };
                
                /**
                 * Close skill detail modal
                 */
                const closeModal = () => {
                    selectedSkill.value = null;
                    activeUseCaseIndex.value = 0;
                    document.body.style.overflow = '';
                };
                
                /**
                 * Copy install command to clipboard
                 * @param {string} skillName - Skill name
                 */
                const copyInstallCommand = async (skillName) => {
                    const lang = document.documentElement.getAttribute('data-lang') || 'zh';
                    const command = lang === 'en' 
                        ? `Please install ${skillName} skill from https://github.com/shetengteng/skillix-hub`
                        : `帮我从 https://github.com/shetengteng/skillix-hub 安装 ${skillName} skill`;
                    
                    try {
                        await navigator.clipboard.writeText(command);
                        // Show a brief feedback (could be enhanced with a toast notification)
                        const btn = event.currentTarget;
                        const originalBg = btn.style.borderColor;
                        btn.style.borderColor = '#22c55e';
                        btn.style.boxShadow = '0 0 0 3px rgba(34, 197, 94, 0.2)';
                        setTimeout(() => {
                            btn.style.borderColor = originalBg;
                            btn.style.boxShadow = '';
                        }, 1000);
                    } catch (err) {
                        console.error('Failed to copy:', err);
                    }
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
                    activeUseCaseIndex,
                    getIconPath,
                    showSkillDetail,
                    closeModal,
                    copyInstallCommand
                };
            }
        }).mount('#skills-app');
    }
    
    // Export initSkillsApp to global scope for external initialization
    window.initSkillsApp = initSkillsApp;

})();
