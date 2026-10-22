// Reviewed rollback worker: retire only Ajiri's public offline cache.
// see docs/CONCEPTS.md#private-safe-pwa
self.addEventListener('install', (event) => event.waitUntil(self.skipWaiting()))
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key.startsWith('ajiri-public-'))
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.registration.unregister())
  )
})
