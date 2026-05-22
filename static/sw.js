self.addEventListener('install', (e) => {
    console.log('[Service Worker] Installed');
});

self.addEventListener('fetch', (e) => {
    // Browsers require a fetch event listener to trigger the "Install App" prompt
    e.respondWith(fetch(e.request));
});