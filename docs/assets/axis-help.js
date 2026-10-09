(function () {
  var installPrompt = null;
  var isStandalone = (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches)
    || window.navigator.standalone === true;

  function installInstructions() {
    if (/iphone|ipad|ipod/i.test(navigator.userAgent)) {
      return 'In Safari, tap Share, then choose Add to Home Screen.';
    }
    if (/firefox/i.test(navigator.userAgent)) {
      return 'Open the browser menu and choose Install or Add to Home Screen if available.';
    }
    return 'Open the browser menu and choose Install app or Add to Home screen.';
  }

  function createInstallControl() {
    if (isStandalone || document.getElementById('axisHelpInstallButton')) return;

    var button = document.createElement('button');
    button.id = 'axisHelpInstallButton';
    button.className = 'axis-help-install';
    button.type = 'button';
    button.setAttribute('aria-haspopup', 'dialog');
    button.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v12m0 0 5-5m-5 5-5-5M5 20h14"/></svg><span>Install AXIS Help</span>';

    var dialog = document.createElement('div');
    dialog.className = 'axis-help-install-dialog';
    dialog.id = 'axisHelpInstallDialog';
    dialog.hidden = true;
    dialog.setAttribute('role', 'dialog');
    dialog.setAttribute('aria-modal', 'true');
    dialog.setAttribute('aria-labelledby', 'axisHelpInstallTitle');
    dialog.innerHTML = '<div class="axis-help-install-card"><button class="axis-help-install-close" type="button" aria-label="Close">×</button><h2 id="axisHelpInstallTitle">Install AXIS Help</h2><p>Read the school guides from your home screen. The Help Center is read-only and keeps its content separate from school and staff records.</p><p class="axis-help-install-tip"></p><button class="axis-help-install-done" type="button">Got it</button></div>';

    function closeDialog() {
      dialog.hidden = true;
      button.focus();
    }

    function showInstructions() {
      dialog.querySelector('.axis-help-install-tip').textContent = installInstructions();
      dialog.hidden = false;
      dialog.querySelector('.axis-help-install-close').focus();
    }

    button.addEventListener('click', async function () {
      if (!installPrompt) {
        showInstructions();
        return;
      }
      var promptEvent = installPrompt;
      installPrompt = null;
      await promptEvent.prompt();
      var choice = await promptEvent.userChoice;
      if (choice && choice.outcome === 'accepted') {
        button.remove();
      } else {
        showInstructions();
      }
    });

    dialog.querySelector('.axis-help-install-close').addEventListener('click', closeDialog);
    dialog.querySelector('.axis-help-install-done').addEventListener('click', closeDialog);
    dialog.addEventListener('click', function (event) {
      if (event.target === dialog) closeDialog();
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && !dialog.hidden) closeDialog();
    });

    document.body.appendChild(button);
    document.body.appendChild(dialog);
  }

  if (!isStandalone) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', createInstallControl, { once: true });
    } else {
      createInstallControl();
    }
  }

  window.addEventListener('beforeinstallprompt', function (event) {
    event.preventDefault();
    installPrompt = event;
  });

  window.addEventListener('appinstalled', function () {
    var button = document.getElementById('axisHelpInstallButton');
    if (button) button.remove();
  });

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('/help/sw.js', { scope: '/help/' })
        .catch(function (error) {
          console.warn('[AXIS Help] Offline support could not start:', error);
        });
    });
  }
})();
