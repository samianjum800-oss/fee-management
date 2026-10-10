(function () {
    'use strict';

    var pendingForms = new WeakSet();

    function createDialog() {
        var dialog = document.createElement('dialog');
        dialog.className = 'axis-confirm-dialog';
        dialog.setAttribute('aria-labelledby', 'axisConfirmTitle');
        dialog.innerHTML = [
            '<form method="dialog" class="axis-confirm-card">',
            '<h2 id="axisConfirmTitle"></h2>',
            '<p class="axis-confirm-message"></p>',
            '<div class="axis-confirm-actions">',
            '<button type="submit" value="cancel" class="axis-confirm-cancel">Cancel</button>',
            '<button type="submit" value="confirm" class="axis-confirm-accept">Continue</button>',
            '</div>',
            '</form>'
        ].join('');
        document.body.appendChild(dialog);
        return dialog;
    }

    var dialog = null;

    function confirmAction(message, options) {
        options = options || {};
        if (!dialog) dialog = createDialog();

        dialog.querySelector('#axisConfirmTitle').textContent = options.title || 'Please confirm';
        dialog.querySelector('.axis-confirm-message').textContent = message;
        var accept = dialog.querySelector('.axis-confirm-accept');
        accept.textContent = options.confirmLabel || 'Continue';
        accept.classList.toggle('is-danger', Boolean(options.danger));

        return new Promise(function (resolve) {
            function finish() {
                dialog.removeEventListener('close', finish);
                resolve(dialog.returnValue === 'confirm');
            }
            dialog.addEventListener('close', finish, { once: true });
            dialog.returnValue = 'cancel';
            dialog.showModal();
            dialog.querySelector('.axis-confirm-cancel').focus();
        });
    }

    window.axisConfirmAction = confirmAction;

    document.addEventListener('submit', function (event) {
        var form = event.target;
        if (!(form instanceof HTMLFormElement) || !form.dataset.confirm) return;

        if (pendingForms.has(form)) {
            pendingForms.delete(form);
            return;
        }

        event.preventDefault();
        event.stopImmediatePropagation();
        var submitter = event.submitter;
        confirmAction(form.dataset.confirm, {
            title: form.dataset.confirmTitle,
            confirmLabel: form.dataset.confirmLabel,
            danger: form.dataset.confirmDanger === 'true'
        }).then(function (confirmed) {
            if (!confirmed) return;
            pendingForms.add(form);
            if (submitter && submitter.form === form) {
                form.requestSubmit(submitter);
            } else {
                form.requestSubmit();
            }
        });
    }, true);
})();
