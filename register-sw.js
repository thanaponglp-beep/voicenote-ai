// service worker registration — เปิดใช้เมื่อ deploy แบบ HTTPS (GitHub Pages)
if ('serviceWorker' in navigator && location.protocol === 'https:') {
  window.addEventListener('load', () => navigator.serviceWorker.register('./sw.js'));
}
