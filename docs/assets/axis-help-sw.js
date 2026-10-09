const CACHE_NAME = 'axis-help-v1';
const CACHE_LIST_URL = '/help/cache-manifest.json';
const HELP_HOME = '/help/';

self.addEventListener('install', function (event) {
  event.waitUntil((async function () {
    const response = await fetch(CACHE_LIST_URL, { cache: 'no-store' });
    if (!response.ok) throw new Error('Help Center cache list is unavailable.');
    const data = await response.json();
    const cache = await caches.open(CACHE_NAME);
    const urls = (data.urls || []).filter(function (url) {
      return typeof url === 'string' && url.indexOf('/help/') === 0;
    });
    await Promise.allSettled(urls.map(function (url) {
      return cache.add(url);
    }));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', function (event) {
  event.waitUntil((async function () {
    const keys = await caches.keys();
    await Promise.all(keys.filter(function (key) {
      return key.indexOf('axis-help-') === 0 && key !== CACHE_NAME;
    }).map(function (key) {
      return caches.delete(key);
    }));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', function (event) {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin || url.pathname.indexOf('/help/') !== 0) return;
  if (url.pathname === '/help/sw.js' || url.pathname === CACHE_LIST_URL) return;

  if (request.mode === 'navigate') {
    event.respondWith((async function () {
      try {
        const response = await fetch(request);
        if (response.ok) {
          const cache = await caches.open(CACHE_NAME);
          await cache.put(request, response.clone());
        }
        return response;
      } catch (error) {
        return (await caches.match(request, { ignoreSearch: true }))
          || (await caches.match(HELP_HOME))
          || new Response('AXIS Help is not available offline yet.', {
            status: 503,
            headers: { 'Content-Type': 'text/plain; charset=utf-8' },
          });
      }
    })());
    return;
  }

  event.respondWith((async function () {
    const cached = await caches.match(request, { ignoreSearch: true });
    if (cached) return cached;
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      await cache.put(request, response.clone());
    }
    return response;
  })());
});
