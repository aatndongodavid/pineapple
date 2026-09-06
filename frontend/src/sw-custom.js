// frontend/src/sw-custom.js

import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { StaleWhileRevalidate, CacheFirst, NetworkOnly } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import { setCacheNameDetails, clientsClaim } from 'workbox-core';

// Active la prise de contrôle immédiate du service worker
clientsClaim();

// Nettoie les anciens caches obsolètes
cleanupOutdatedCaches();

// Pré‑cache du manifest généré par VitePWA
precacheAndRoute(self.__WB_MANIFEST);

// ---------------------------------------------------------------------------
// Stratégie 1 : CacheFirst pour les assets statiques (fonts, images, CSS, JS)
// Ces ressources sont versionnées et ne changent pas souvent.
// ---------------------------------------------------------------------------
registerRoute(
  ({ request }) =>
    request.destination === 'font' ||
    request.destination === 'image' ||
    request.destination === 'style' ||
    request.destination === 'script',
  new CacheFirst({
    cacheName: 'static-assets',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 30 * 24 * 60 * 60, // 30 jours
      }),
    ],
  })
);

// ---------------------------------------------------------------------------
// Stratégie 2 : StaleWhileRevalidate pour les requêtes GET non critiques
// (Feed, salles, bibliothèque, opportunités)
// L'utilisateur voit le contenu en cache pendant que le réseau est sollicité.
// ---------------------------------------------------------------------------
const nonCriticalApiRoutes = [
  /\/api\/v1\/community\/feed/,
  /\/api\/v1\/community\/rooms/,
  /\/api\/v1\/academy\/library/,
  /\/api\/v1\/opportunities/,
];

nonCriticalApiRoutes.forEach((route) => {
  registerRoute(
    route,
    new StaleWhileRevalidate({
      cacheName: 'api-cache',
      plugins: [
        new ExpirationPlugin({
          maxEntries: 50,
          maxAgeSeconds: 5 * 60, // 5 minutes
        }),
      ],
    })
  );
});

// ---------------------------------------------------------------------------
// Stratégie 3 : NetworkOnly pour toutes les requêtes non‑GET (actions critiques)
// Vote, achat, vérification de statut, envoi de message, etc.
// Aucune mise en cache pour ces opérations.
// ---------------------------------------------------------------------------
registerRoute(
  ({ request }) => request.method !== 'GET',
  new NetworkOnly()
);

// ---------------------------------------------------------------------------
// Gestion d'un fallback hors ligne pour les pages de l'application
// (en cas de navigation et d'absence de cache)
// ---------------------------------------------------------------------------
// (Optionnel) Pour une PWA, on peut servir une page offline pré‑cachée.
// Ici on suppose qu'une page "offline.html" existe dans le build.
const offlineFallback = async ({ request }) => {
  const cached = await caches.match(request);
  if (cached) return cached;
  return caches.match('offline.html') || Response.error();
};

// Pour la navigation, on utilise NetworkFirst avec fallback offline
import { NetworkFirst } from 'workbox-strategies';

registerRoute(
  ({ request }) => request.mode === 'navigate',
  new NetworkFirst({
    cacheName: 'pages-cache',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 10,
        maxAgeSeconds: 7 * 24 * 60 * 60,
      }),
    ],
  })
);

// ---------------------------------------------------------------------------
// Écoute des messages pour forcer la mise à jour du service worker
// ---------------------------------------------------------------------------
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});