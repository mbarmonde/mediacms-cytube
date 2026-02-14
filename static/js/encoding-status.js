// dev-v0.1.7 - Real-time encoding widget status

/////
//- Encoding Status Widget - With ETA and CyTube Ready Status
/////

(function() {
    'use strict';
    
    console.log('[Encoding Widget] Script loaded v1.7');
    
    if (!window.location.pathname.includes('/view')) {
        return;
    }
    
    const urlParams = new URLSearchParams(window.location.search);
    const mediaUid = urlParams.get('m');
    
    if (!mediaUid) {
        return;
    }
    
    console.log('[Encoding Widget] Media UID:', mediaUid);
    
    // Create status container
    const statusDiv = document.createElement('div');
    statusDiv.id = 'encoding-status-widget';
    statusDiv.style.cssText = `
        position: fixed;
        bottom: 220px;
        right: 20px;
        background: linear-gradient(135deg, rgba(0, 0, 0, 0.95), rgba(30, 30, 30, 0.95));
        color: white;
        padding: 16px;
        border-radius: 12px;
        width: 300px;
        z-index: 9998;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
        font-size: 14px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        border: 1px solid rgba(255,255,255,0.15);
        transition: opacity 0.3s, transform 0.3s;
    `;
    
    document.body.appendChild(statusDiv);
    
    let refreshInterval = null;
    let updateCount = 0;
    let isExpanded = false;
    
    // ETA tracking
    let progressHistory = []; // [{timestamp, completed, total}]
    let estimatedSecondsRemaining = null;
    
    function getStatusEmoji(status) {
        const s = (status || '').toLowerCase();
        if (s === 'success' || s === 'complete') return '✅';
        if (s === 'fail' || s === 'error') return '❌';
        if (s === 'running') return '⏳';
        return '⏸️';
    }
    
    function getStatusColor(status) {
        const s = (status || '').toLowerCase();
        if (s === 'success' || s === 'complete') return '#4CAF50';
        if (s === 'fail' || s === 'error') return '#f44336';
        if (s === 'running') return '#FFA726';
        return '#64B5F6';
    }
    
    function getStatusText(status) {
        const s = (status || '').toLowerCase();
        if (s === 'success' || s === 'complete') return 'Complete';
        if (s === 'fail' || s === 'error') return 'Failed';
        if (s === 'running') return 'Encoding...';
        if (s === 'pending' || s === 'queued') return 'Queued';
        return 'Unknown';
    }
    
    function formatTimeRemaining(seconds) {
        if (!seconds || seconds <= 0) return 'Calculating...';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }
    
    function calculateETA(completed, total) {
        const now = Date.now();
        
        // Add current progress to history
        progressHistory.push({
            timestamp: now,
            completed: completed,
            total: total
        });
        
        // Keep only last 5 data points (15 seconds of history at 3s intervals)
        if (progressHistory.length > 5) {
            progressHistory.shift();
        }
        
        // Need at least 2 data points to calculate rate
        if (progressHistory.length < 2) {
            return null;
        }
        
        // Calculate encoding rate (profiles per second)
        const oldest = progressHistory[0];
        const newest = progressHistory[progressHistory.length - 1];
        
        const timeElapsed = (newest.timestamp - oldest.timestamp) / 1000; // seconds
        const progressMade = newest.completed - oldest.completed;
        
        if (progressMade <= 0 || timeElapsed <= 0) {
            return estimatedSecondsRemaining; // Return last known estimate
        }
        
        const profilesPerSecond = progressMade / timeElapsed;
        const profilesRemaining = total - completed;
        
        estimatedSecondsRemaining = profilesRemaining / profilesPerSecond;
        
        return estimatedSecondsRemaining;
    }
    
    function updateStatus() {
        updateCount++;
        console.log(`[Encoding Widget] Update #${updateCount}`);
        
        const apiUrl = `/api/encoding-status/${mediaUid}/`;
        
        fetch(apiUrl, {
            credentials: 'include',
            cache: 'no-cache'
        })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log('[Encoding Widget] Data:', data);
            
            if (!data.encodings || data.encodings.length === 0) {
                statusDiv.innerHTML = `
                    <div style="text-align: center;">
                        <strong style="font-size: 16px;">✅ Encoding Complete</strong><br>
                        <div style="margin-top: 12px; padding: 10px; background: linear-gradient(135deg, rgba(76, 175, 80, 0.2), rgba(56, 142, 60, 0.2)); border-radius: 8px; border: 2px solid #4CAF50;">
                            <div style="font-size: 14px; color: #4CAF50; font-weight: bold; margin-bottom: 4px;">
                                🎬 Ready for Export to CyTube!
                            </div>
                            <div style="font-size: 11px; color: #aaa;">
                                Use the button below to export
                            </div>
                        </div>
                        <div style="margin-top: 8px; font-size: 10px; color: #666;">
                            ${new Date().toLocaleTimeString()}
                        </div>
                    </div>
                `;
                // Clear history when done
                progressHistory = [];
                estimatedSecondsRemaining = null;
                return;
            }
            
            // Sort encodings
            const encodings = data.encodings.sort((a, b) => {
                const order = { 'running': 0, 'pending': 1, 'queued': 2, 'success': 3, 'fail': 4 };
                const statusA = (a.status || '').toLowerCase();
                const statusB = (b.status || '').toLowerCase();
                return (order[statusA] || 5) - (order[statusB] || 5);
            });
            
            const total = encodings.length;
            const completed = encodings.filter(e => ['success', 'complete'].includes((e.status || '').toLowerCase())).length;
            const failed = encodings.filter(e => ['fail', 'error'].includes((e.status || '').toLowerCase())).length;
            const running = encodings.filter(e => (e.status || '').toLowerCase() === 'running').length;
            const pending = encodings.filter(e => ['pending', 'queued'].includes((e.status || '').toLowerCase())).length;
            
            // Calculate percentage
            const percentage = Math.round((completed / total) * 100);
            
            // Calculate ETA if encoding is active
            let etaSeconds = null;
            if (running > 0 || pending > 0) {
                etaSeconds = calculateETA(completed, total);
            } else {
                // Clear history when not encoding
                progressHistory = [];
                estimatedSecondsRemaining = null;
            }
            
            // Check if 100% complete (all success, none running/pending)
            const isFullyComplete = percentage === 100 && running === 0 && pending === 0 && failed === 0;
            
            // Compact mode (default)
            let html = `
                <div style="cursor: pointer;" onclick="document.getElementById('encoding-status-widget').dataset.expanded = document.getElementById('encoding-status-widget').dataset.expanded === 'true' ? 'false' : 'true'; window.encodingWidgetUpdate();">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <strong style="font-size: 15px;">🎬 Encoding</strong>
                        <span style="font-size: 13px; ${isFullyComplete ? 'color: #4CAF50' : 'color: #FFA726'}; font-weight: bold;">${percentage}%</span>
                    </div>
                    
                    <div style="background: rgba(255,255,255,0.1); height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 8px;">
                        <div style="background: ${isFullyComplete ? '#4CAF50' : 'linear-gradient(90deg, #4CAF50, #FFA726)'}; height: 100%; width: ${percentage}%; transition: width 0.5s ease;"></div>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; font-size: 12px; color: #aaa; margin-bottom: 8px;">
                        <span>${completed}/${total} complete</span>
                        ${running > 0 ? `<span style="color: #FFA726;">⏳ ${running} encoding</span>` : ''}
                        ${pending > 0 ? `<span style="color: #64B5F6;">⏸️ ${pending} queued</span>` : ''}
                        ${failed > 0 ? `<span style="color: #f44336;">❌ ${failed} failed</span>` : ''}
                    </div>
            `;
            
            // Show "Ready for CyTube" when 100% complete
            if (isFullyComplete) {
                html += `
                    <div style="padding: 10px; background: linear-gradient(135deg, rgba(76, 175, 80, 0.2), rgba(56, 142, 60, 0.2)); border-radius: 8px; border: 2px solid #4CAF50; margin-bottom: 8px;">
                        <div style="font-size: 13px; color: #4CAF50; font-weight: bold; text-align: center;">
                            🎬 Ready for Export to CyTube!
                        </div>
                    </div>
                `;
            }
            
            // Add ETA display (only if encoding in progress)
            if (etaSeconds !== null && (running > 0 || pending > 0)) {
                html += `
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px; background: rgba(255,165,0,0.1); border-radius: 4px; border-left: 3px solid #FFA726; margin-bottom: 8px;">
                        <span style="font-size: 12px; color: #aaa;">⏱️ Time remaining:</span>
                        <span style="font-size: 13px; color: #FFA726; font-weight: bold;">${formatTimeRemaining(etaSeconds)}</span>
                    </div>
                `;
            }
            
            // Add expandable details
            if (isExpanded) {
                html += `
                    <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.2); margin: 12px 0;">
                    <div style="font-size: 12px; color: #888; margin-bottom: 8px;">Details:</div>
                `;
                
                encodings.forEach((enc, i) => {
                    const profile = enc.profile_name || `Profile ${i + 1}`;
                    const status = enc.status || 'unknown';
                    const emoji = getStatusEmoji(status);
                    const statusText = getStatusText(status);
                    const color = getStatusColor(status);
                    
                    html += `
                        <div style="margin: 6px 0; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 4px; border-left: 3px solid ${color}; font-size: 12px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span>${emoji} ${profile}</span>
                                <span style="color: ${color}; font-weight: bold;">${statusText}</span>
                            </div>
                        </div>
                    `;
                });
            } else {
                html += `
                    <div style="text-align: center; font-size: 11px; color: #666; margin-top: 8px;">
                        Click to expand
                    </div>
                `;
            }
            
            // Add timestamp
            html += `
                <div style="text-align: right; font-size: 10px; color: #555; margin-top: 8px;">
                    ${new Date().toLocaleTimeString()}
                </div>
            `;
            
            html += `</div>`;
            
            statusDiv.innerHTML = html;
            statusDiv.dataset.expanded = isExpanded ? 'true' : 'false';
        })
        .catch(err => {
            console.error('[Encoding Widget] Error:', err);
            statusDiv.innerHTML = `
                <div style="text-align: center;">
                    <strong style="color: #f44336;">❌ Status Unavailable</strong><br>
                    <div style="margin-top: 8px; font-size: 12px; color: #aaa;">
                        ${err.message}
                    </div>
                    <div style="margin-top: 8px; font-size: 10px; color: #666;">
                        ${new Date().toLocaleTimeString()}
                    </div>
                </div>
            `;
        });
    }
    
    // Global function to handle expand/collapse
    window.encodingWidgetUpdate = function() {
        isExpanded = statusDiv.dataset.expanded === 'true';
        updateStatus();
    };
    
    // Initial update
    setTimeout(updateStatus, 1000);
    
    // Refresh every 3 seconds
    console.log('[Encoding Widget] Starting auto-refresh every 3 seconds');
    refreshInterval = setInterval(updateStatus, 3000);
    
    // Cleanup
    window.addEventListener('beforeunload', () => {
        if (refreshInterval) clearInterval(refreshInterval);
    });
})();
