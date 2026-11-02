'use strict';
const NAME = 'hamapp-shell-v1';
const SHELL = ['./', './index.html', './styles.css', './app.js', './icon.svg', './icon-192.png', './icon-512.png', './manifest.webmanifest'];
self.addEventListener('install', event => event.waitUntil(caches.open(NAME).then(cache => cache.addAll(SHELL)).then(() => self.skipWaiting())));
self.addEventListener('activate', event => event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('hamapp-shell-') && k !== NAME).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('fetch', event => {
  const u = new URL(event.request.url);
  if(event.request.method !== 'GET' || u.origin !== self.location.origin || /\.(apk|exe|msi|zip)$/i.test(u.pathname)) return;
  if(u.pathname.endsWith('/catalog/apps.json')) {event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));return;}
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
