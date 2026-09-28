/**
 * StegoShield Service Worker
 * Version: 1.0.0
 * Provides offline application shell caching and graceful connectivity fallbacks.
 */

const CACHE_NAME = 'stegoshield-cache-v1';

const APP_SHELL_ASSETS = [
  '/',
  '/hide',
  '/extract',
  '/how-it-works',
  '/security',
  '/offline',
  '/manifest.json',
  '/static/css/style.css',
  '/static/js/app.js',
  '/static/js/hide.js',
  '/static/js/extract.js',
  '/static/images/logo.svg',
  '/static/images/icons/icon-192.png',
  '/static/images/icons/icon-512.png',
  '/static/images/icons/apple-touch-icon.png',
  '/static/images/icons/favicon-32.png'
];

// Install: Pre-cache application shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // Use catch on each item so a single failure doesn't abort the entire install
      return Promise.allSettled(
        APP_SHELL_ASSETS.map((url) =>
          cache.add(url).catch((err) => {
            console.warn(`[SW] Pre-cache skipped for ${url}:`, err);
          })
        )
      );
    }).then(() => self.skipWaiting())
  );
});

// Activate: Purge stale caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch: Strategy depending on request type
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // Never cache API endpoints or download streams
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/download/')) {
    return;
  }

  // Non-GET requests should always bypass cache
  if (request.method !== 'GET') {
    return;
  }

  // Navigation requests (HTML pages): Network-First with Cached Fallback and Offline Page
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((networkResponse) => {
          // Clone and store fresh copy in cache
          if (networkResponse && networkResponse.status === 200) {
            const copy = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          }
          return networkResponse;
        })
        .catch(async () => {
          // If offline, check cache for requested page
          const cachedResponse = await caches.match(request);
          if (cachedResponse) {
            return cachedResponse;
          }
          // Return generic offline page if specific page wasn't cached
          const offlinePage = await caches.match('/offline');
          return offlinePage || new Response('Offline - No connection available', {
            status: 503,
            headers: { 'Content-Type': 'text/plain' }
          });
        })
    );
    return;
  }

  // Static assets (CSS, JS, Images, Fonts): Stale-While-Revalidate
  if (
    url.pathname.startsWith('/static/') ||
    url.hostname.includes('fonts.googleapis.com') ||
    url.hostname.includes('fonts.gstatic.com')
  ) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        const fetchPromise = fetch(request)
          .then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200) {
              const copy = networkResponse.clone();
              caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
            }
            return networkResponse;
          })
          .catch(() => cachedResponse);

        return cachedResponse || fetchPromise;
      })
    );
    return;
  }

  // Default: Network with cache fallback
  event.respondWith(
    fetch(request).catch(() => caches.match(request))
  );
});
