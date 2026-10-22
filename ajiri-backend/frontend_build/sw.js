// Cache only this explicit public fallback set. Never store API/account content.
// see docs/CONCEPTS.md#private-safe-pwa
const CACHE = 'ajiri-public-v1'
const PUBLIC = [
  '/offline.html',
  '/manifest.webmanifest',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
]
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) =>
        cache.addAll(
          PUBLIC.map(
            (path) =>
              new Request(path, { credentials: 'omit', cache: 'reload' })
          )
        )
      )
      .then(() => self.skipWaiting())
  )
})
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key.startsWith('ajiri-public-') && key !== CACHE)
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  )
})
self.addEventListener('fetch', (event) => {
  const request = event.request
  const url = new URL(request.url)
  if (request.method !== 'GET' || url.origin !== self.location.origin) return
  if (
    ['/api', '/media', '/admin', '/static'].some(
      (prefix) =>
        url.pathname === prefix || url.pathname.startsWith(prefix + '/')
    )
  )
    return
  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).catch(() => caches.match('/offline.html')))
  } else if (!url.search && PUBLIC.includes(url.pathname)) {
    event.respondWith(
      caches.match(request).then((cached) => cached || fetch(request))
    )
  }
})
