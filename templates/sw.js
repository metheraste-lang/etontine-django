const CACHE_NOM = 'etontine-cache-v1';
const URLS_HORS_LIGNE = ['/tableau-de-bord/'];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NOM).then((cache) => cache.addAll(URLS_HORS_LIGNE)).catch(() => {})
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    if (event.request.method !== 'GET') return;
    event.respondWith(
        fetch(event.request)
            .then((reponse) => {
                const copie = reponse.clone();
                caches.open(CACHE_NOM).then((cache) => cache.put(event.request, copie)).catch(() => {});
                return reponse;
            })
            .catch(() => caches.match(event.request))
    );
});
