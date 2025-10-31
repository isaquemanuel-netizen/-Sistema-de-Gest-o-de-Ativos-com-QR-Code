/**
 * SERVICE WORKER - PWA
 * Sistema de Gestão de Ativos
 */

const CACHE_NAME = 'ativos-qr-v1.0.0';
const OFFLINE_URL = '/offline';

// Arquivos essenciais para cache
const ESSENTIAL_FILES = [
  '/',
  '/dashboard',
  '/ativos',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/manifest.json',
  '/static/logo.png'
];

// Cache de recursos externos (CDN)
const CDN_RESOURCES = [
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css',
  'https://code.jquery.com/jquery-3.7.1.min.js',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
  'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js'
];

// ========================================
// INSTALL - Cache inicial
// ========================================
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Install');

  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE_NAME);

      try {
        // Cache arquivos essenciais
        await cache.addAll(ESSENTIAL_FILES);
        console.log('[ServiceWorker] Essential files cached');

        // Cache CDN resources (não bloqueia se falhar)
        await Promise.allSettled(
          CDN_RESOURCES.map(url =>
            cache.add(url).catch(err => console.warn(`[ServiceWorker] Failed to cache ${url}`, err))
          )
        );
        console.log('[ServiceWorker] CDN resources cached');
      } catch (error) {
        console.error('[ServiceWorker] Cache failed:', error);
      }

      // Força o service worker a ativar imediatamente
      self.skipWaiting();
    })()
  );
});

// ========================================
// ACTIVATE - Limpar caches antigos
// ========================================
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activate');

  event.waitUntil(
    (async () => {
      // Limpar caches antigos
      const cacheNames = await caches.keys();
      await Promise.all(
        cacheNames
          .filter(name => name !== CACHE_NAME)
          .map(name => {
            console.log('[ServiceWorker] Deleting old cache:', name);
            return caches.delete(name);
          })
      );

      // Tomar controle de todas as páginas imediatamente
      await self.clients.claim();
    })()
  );
});

// ========================================
// FETCH - Estratégia de cache
// ========================================
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignorar requisições não-GET
  if (request.method !== 'GET') {
    return;
  }

  // Ignorar requisições de API/POST
  if (url.pathname.includes('/add') ||
      url.pathname.includes('/editar') ||
      url.pathname.includes('/deletar') ||
      url.pathname.includes('/upload')) {
    return;
  }

  // Estratégia: Network First com Cache Fallback
  event.respondWith(
    (async () => {
      try {
        // Tentar buscar da rede
        const networkResponse = await fetch(request);

        // Se sucesso, atualizar cache
        if (networkResponse && networkResponse.status === 200) {
          const cache = await caches.open(CACHE_NAME);

          // Clonar response antes de cachear
          cache.put(request, networkResponse.clone());
        }

        return networkResponse;
      } catch (error) {
        // Se falhar, buscar do cache
        console.log('[ServiceWorker] Fetch failed, using cache:', request.url);

        const cachedResponse = await caches.match(request);

        if (cachedResponse) {
          return cachedResponse;
        }

        // Se não houver cache, retornar página offline para navegação
        if (request.destination === 'document') {
          const offlineResponse = await caches.match(OFFLINE_URL);
          if (offlineResponse) {
            return offlineResponse;
          }
        }

        // Último recurso: erro
        return new Response('Offline - conteúdo não disponível', {
          status: 503,
          statusText: 'Service Unavailable',
          headers: new Headers({
            'Content-Type': 'text/plain'
          })
        });
      }
    })()
  );
});

// ========================================
// BACKGROUND SYNC (futuro)
// ========================================
self.addEventListener('sync', (event) => {
  console.log('[ServiceWorker] Background sync:', event.tag);

  if (event.tag === 'sync-ativos') {
    event.waitUntil(syncAtivos());
  }
});

async function syncAtivos() {
  try {
    // Implementação futura: sincronizar dados offline
    console.log('[ServiceWorker] Syncing ativos...');
  } catch (error) {
    console.error('[ServiceWorker] Sync failed:', error);
  }
}

// ========================================
// PUSH NOTIFICATIONS (futuro)
// ========================================
self.addEventListener('push', (event) => {
  console.log('[ServiceWorker] Push notification received');

  const data = event.data ? event.data.json() : {};
  const title = data.title || 'Sistema de Ativos';
  const options = {
    body: data.body || 'Nova notificação',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-72x72.png',
    vibrate: [200, 100, 200],
    data: data,
    actions: data.actions || []
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// ========================================
// NOTIFICATION CLICK
// ========================================
self.addEventListener('notificationclick', (event) => {
  console.log('[ServiceWorker] Notification clicked');

  event.notification.close();

  const url = event.notification.data?.url || '/';

  event.waitUntil(
    clients.openWindow(url)
  );
});

// ========================================
// MESSAGE - Comunicação com a página
// ========================================
self.addEventListener('message', (event) => {
  console.log('[ServiceWorker] Message received:', event.data);

  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CACHE_URLS') {
    event.waitUntil(
      caches.open(CACHE_NAME).then(cache => {
        return cache.addAll(event.data.urls);
      })
    );
  }
});

console.log('[ServiceWorker] Loaded and ready');
