self.addEventListener('push', e => {
  const d = e.data?.json() || {};
  e.waitUntil(self.registration.showNotification(d.title || 'MYRO', {
    body: d.body || '',
    icon: '/myro/og-image.png',
    badge: '/myro/og-image.png',
    vibrate: [200, 100, 200],
    tag: 'myro-' + (d.tag || 'routine'),
    requireInteraction: false,
  }));
});

self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil(clients.openWindow('https://myro-official.github.io/myro/app.html'));
});
