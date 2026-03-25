// Browser Console Script to Find ON24 VTT Subtitle URL
// Run this in DevTools Console (F12) on the ON24 video page

(function() {
    console.log('🔍 Searching for VTT subtitle files...');
    
    // Check existing network resources
    performance.getEntriesByType('resource').forEach(entry => {
        if (entry.name.includes('.vtt') || entry.name.includes('.srt') || 
            entry.name.includes('caption') || entry.name.includes('subtitle')) {
            console.log('🎯 Found:', entry.name);
        }
    });
    
    // Monitor for new subtitle requests
    let originalFetch = window.fetch;
    window.fetch = function(...args) {
        let url = args[0];
        if (typeof url === 'string' && (url.includes('.vtt') || url.includes('.srt') || url.includes('caption'))) {
            console.log('🎯 Subtitle URL:', url);
            alert('Found VTT URL: ' + url);
        }
        return originalFetch.apply(this, args);
    };
    
    console.log('✓ Monitoring for subtitle files... Play the video if needed.');
})();
