// dev-v0.1.0

/////
//- Initial release
/////

// Stored at: /mediacms/media_files/cytube-export.js
// This file is served from Caddy via the Docker Compose volume mapping of Caddy to the media folder
// Creates custom CyTube Export Manifest button

(function() {
    'use strict';
    
    // Only run on video pages
    if (!window.location.pathname.includes('/view') && !window.location.search.includes('m=')) {
        return;
    }
    
    let buttonInjected = false;
    
    function createFloatingButton() {
        // Double-check it doesn't exist
        if (document.getElementById('cytube-export-container')) {
            console.log('✅ Button already exists, skipping');
            return;
        }

        console.log('🔧 Creating floating CyTube button...');

        // Create a completely isolated container
        const container = document.createElement('div');
        container.id = 'cytube-export-container';
        
        // Use setAttribute to force styles
        container.setAttribute('style', `
            position: fixed !important;
            bottom: 20px !important;
            right: 20px !important;
            z-index: 2147483647 !important;
            padding: 16px !important;
            background: rgba(0, 0, 0, 0.95) !important;
            border-radius: 8px !important;
            border: 2px solid #4CAF50 !important;
            max-width: 280px !important;
            text-align: center !important;
            color: #fff !important;
            box-shadow: 0 8px 24px rgba(0,0,0,0.6) !important;
            pointer-events: auto !important;
            display: block !important;
            font-family: Arial, sans-serif !important;
            transform: translateZ(0) !important;
        `);

        const title = document.createElement('div');
        title.textContent = 'CyTube Export';
        title.setAttribute('style', `
            font-weight: bold !important;
            margin-bottom: 12px !important;
            color: #fff !important;
            font-size: 16px !important;
            display: block !important;
        `);

        const button = document.createElement('button');
        button.id = 'cytube-export-btn';
        button.textContent = '📥 Export for CyTube';
        button.setAttribute('style', `
            padding: 12px 24px !important;
            background-color: #4CAF50 !important;
            color: white !important;
            border: none !important;
            border-radius: 4px !important;
            cursor: pointer !important;
            font-size: 16px !important;
            font-weight: bold !important;
            transition: background-color 0.3s !important;
            width: 100% !important;
            display: block !important;
        `);

        button.onmouseover = function() {
            this.style.backgroundColor = '#45a049';
        };
        button.onmouseout = function() {
            this.style.backgroundColor = '#4CAF50';
        };

        button.addEventListener('click', async function() {
            try {
                const urlParams = new URLSearchParams(window.location.search);
                const friendlyToken = urlParams.get('m');

                if (!friendlyToken) {
                    alert('Cannot determine video ID from URL');
                    return;
                }

                button.disabled = true;
                button.textContent = '⏳ Generating...';
                button.style.backgroundColor = '#999';

                const apiUrl = window.location.origin + '/api/v1/media/' + friendlyToken + '/cytube-manifest/';
                console.log('Calling API:', apiUrl);

                const response = await fetch(apiUrl);

                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('API error:', errorText);
                    throw new Error('Failed to generate manifest: ' + response.status);
                }

                const data = await response.json();
                const jsonUrl = data.json_url;

                // Only copy to clipboard - no download
                await navigator.clipboard.writeText(jsonUrl);

                button.disabled = false;
                button.textContent = '✅ Copied!';
                button.style.backgroundColor = '#4CAF50';

                setTimeout(() => {
                    button.textContent = '📥 Export for CyTube';
                }, 3000);

                alert('✅ CyTube manifest URL copied to clipboard:\n\n' + jsonUrl);

            } catch (error) {
                console.error('Error:', error);
                button.disabled = false;
                button.textContent = '❌ Error - Try Again';
                button.style.backgroundColor = '#f44336';

                setTimeout(() => {
                    button.textContent = '📥 Export for CyTube';
                    button.style.backgroundColor = '#4CAF50';
                }, 3000);

                alert('❌ Failed to generate CyTube manifest:\n\n' + error.message);
            }
        });

        container.appendChild(title);
        container.appendChild(button);

        // CRITICAL: Append directly to <body>, not any child element
        const body = document.querySelector('body');
        body.appendChild(container);
        
        // Verify it's actually attached to body
        console.log('✅ Button parent:', container.parentElement.tagName);
        console.log('✅ Button position:', window.getComputedStyle(container).position);
        console.log('✅ Button z-index:', window.getComputedStyle(container).zIndex);
        
        buttonInjected = true;
    }
    
    // Wait for page to fully load AND React to finish rendering
    window.addEventListener('load', function() {
        console.log('🕒 Page loaded, waiting 2 seconds for React to settle...');
        
        // Delay injection by 2 seconds to let React finish
        setTimeout(function() {
            createFloatingButton();
            
            // Keep monitoring to ensure it stays on body
            setInterval(function() {
                const container = document.getElementById('cytube-export-container');
                if (container && container.parentElement.tagName !== 'BODY') {
                    console.warn('⚠️ Button was moved! Re-attaching to body...');
                    document.body.appendChild(container);
                }
            }, 1000);
        }, 2000);
    });

})();
