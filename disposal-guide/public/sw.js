/* Offline support. Owen may be in a garage with no signal.
 *
 * An app-shell precache plus runtime caching of same-origin GETs. The precache list is injected
 * at build time by scripts/gen-sw.ts rather than maintained by hand, so it cannot drift from
 * what was actually built.
 *
 * Same-origin only, by construction. A cross-origin request never reaches the cache because it
 * never reaches this handler's happy path — see the origin check in fetch.
 */
const VERSION = 'dg-v1';
// Injected at build time by scripts/gen-sw.ts. Without this the hashed assets are only
// cached on the SECOND visit — the first load fetches them before the worker is controlling —
// and "offline" would quietly mean "offline, if you've been here twice".
const SHELL = ['./', './index.html', './manifest.webmanifest', /* __PRECACHE__ */];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(VERSION)
      .then((cache) => cache.addAll(SHELL))
      .then(() => self.skipWaiting())
      .catch(() => self.skipWaiting()),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return; // never cache or proxy third parties

  // Navigations: try the network so a new build is picked up, fall back to cache offline.
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(VERSION).then((c) => c.put('./index.html', copy));
          return res;
        })
        .catch(async () => {
          // ignoreVary/ignoreSearch matter here: a reload's navigation request does not carry
          // the same headers as the precached GET, and a Vary mismatch makes match() return
          // undefined. respondWith(undefined) throws, which shows the browser's offline error
          // page — the exact failure this handler exists to prevent.
          const opts = { ignoreVary: true, ignoreSearch: true };
          const hit =
            (await caches.match('./index.html', opts)) ||
            (await caches.match('./', opts)) ||
            (await caches.match(new URL('./index.html', self.location.href).href, opts));
          return (
            hit ||
            new Response(
              '<!doctype html><meta charset=utf-8><title>Offline</title>' +
                '<p style="font:1.2rem system-ui;padding:1rem">' +
                "You're offline and this page isn't saved on this device yet. " +
                'When in doubt, household hazardous waste is never the wrong answer.</p>',
              { headers: { 'Content-Type': 'text/html; charset=utf-8' }, status: 200 },
            )
          );
        }),
    );
    return;
  }

  // Everything else: cache first. Assets are content-hashed, so a stale hit is a correct hit.
  event.respondWith(
    caches.match(req, { ignoreVary: true }).then(
      (hit) =>
        hit ||
        fetch(req).then((res) => {
          if (res.ok && res.type === 'basic') {
            const copy = res.clone();
            caches.open(VERSION).then((c) => c.put(req, copy));
          }
          return res;
        }),
    ),
  );
});
