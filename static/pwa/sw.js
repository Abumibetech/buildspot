const CACHE = 'buildspot-static-v3';
const FILES = [
  '/static/css/site.css',
  '/static/js/site.js'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(FILES))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key.startsWith('buildspot-') && key !== CACHE)
          .map(key => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;
  if (!url.pathname.startsWith('/static/')) return;

  event.respondWith(
    caches.open(CACHE).then(async cache => {
      const cached = await cache.match(event.request);
      if (cached) return cached;

      const response = await fetch(event.request);

      if (response.ok && response.type === 'basic') {
        await cache.put(event.request, response.clone());
      }

      return response;
    })
  );
});

self.addEventListener('push', event => {
  let data = {};

  try {
    data = event.data ? event.data.json() : {};
  } catch (_) {
    data = { body: event.data ? event.data.text() : '' };
  }

  const title = String(data.title || 'BuildSpot community update').slice(0, 160);
  const body = String(data.body || 'There is a new update for you.').slice(0, 500);

  let target = '/community/';

  if (typeof data.url === 'string' && data.url.startsWith('/') && !data.url.startsWith('//')) {
    target = data.url;
  }

  event.waitUntil(
    self.registration.showNotification(title, {
      body,
      icon: '/static/img/icon-192.png',
      badge: '/static/img/icon-192.png',
      data: { url: target }
    })
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();

  let target = '/community/';
  const supplied = event.notification.data && event.notification.data.url;

  if (typeof supplied === 'string' && supplied.startsWith('/') && !supplied.startsWith('//')) {
    target = supplied;
  }

  event.waitUntil(
    self.clients.openWindow(new URL(target, self.location.origin).href)
  );
});
