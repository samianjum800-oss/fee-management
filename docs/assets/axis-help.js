(function () {
  if (!('serviceWorker' in navigator)) return;

  window.addEventListener('load', function () {
    navigator.serviceWorker.register('/help/sw.js', { scope: '/help/' })
      .catch(function (error) {
        console.warn('[AXIS Help] Offline support could not start:', error);
      });
  });
})();
