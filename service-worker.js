const CACHE_NAME = 'tiktok-downloader-cache-v1';
const urlsToCache = [
    '/',
    '/index.html',
    // ... diger əsas resurslar (CSS, JS)
];

// Quraşdırma (Install) Hadisəsi: Resursları keşə əlavə edir
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Service Worker: Kəşdəki əsas resurslar');
        return cache.addAll(urlsToCache);
      })
      .catch(error => {
          console.error('Service Worker Kəşə əlavə etmə xətası:', error);
      })
  );
});

// Fəallaşma (Activate) Hadisəsi: Köhnə keşləri təmizləyir
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            // Ağ siyahıda olmayan köhnə keşləri sil
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Sorğu (Fetch) Hadisəsi: Keşdən və ya şəbəkədən cavab verir
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Əgər kəşdə cavab varsa, onu qaytar
        if (response) {
          return response;
        }
        // Əks halda, şəbəkəyə müraciət et
        return fetch(event.request);
      })
  );
});