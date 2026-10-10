(function () {
    'use strict';

    var pendingForms = new WeakSet();

    function createDialog() {
        var dialog = document.createElement('dialog');
        dialog.className = 'axis-confirm-dialog';
        dialog.setAttribute('aria-labelledby', 'axisConfirmTitle');
        dialog.setAttribute('aria-describedby', 'axisConfirmMessage');
        dialog.innerHTML = [
            '<form method="dialog" class="axis-confirm-card">',
            '<div class="axis-confirm-heading">',
            '<span class="axis-confirm-icon" aria-hidden="true"></span>',
            '<div><span class="axis-confirm-eyebrow">REVIEW BEFORE YOU CONTINUE</span>',
            '<h2 id="axisConfirmTitle"></h2></div>',
            '</div>',
            '<p class="axis-confirm-message" id="axisConfirmMessage"></p>',
            '<section class="axis-confirm-overview" aria-label="Change overview" hidden>',
            '<h3>Quick overview</h3><ul class="axis-confirm-details"></ul>',
            '</section>',
            '<p class="axis-confirm-footnote">Please review this action before confirming.</p>',
            '<div class="axis-confirm-actions">',
            '<button type="submit" value="cancel" class="axis-confirm-cancel">Cancel</button>',
            '<button type="submit" value="confirm" class="axis-confirm-accept"><span>Continue</span><span aria-hidden="true">→</span></button>',
            '</div>',
            '</form>'
        ].join('');
        document.body.appendChild(dialog);
        dialog.addEventListener('click', function (event) {
            if (event.target === dialog) dialog.close('cancel');
        });
        return dialog;
    }

    var dialog = null;

    function fieldLabel(field) {
        if (field.labels && field.labels.length) {
            return field.labels[0].textContent.trim().replace(/\s+/g, ' ');
        }
        var parentLabel = field.closest('label');
        if (parentLabel) {
            return parentLabel.textContent.replace(field.value || '', '').trim().replace(/\s+/g, ' ');
        }
        return (field.name || 'Updated field').replace(/[_-]+/g, ' ').replace(/\b\w/g, function (letter) {
            return letter.toUpperCase();
        });
    }

    function changedFieldDetails(form) {
        if (!form) return [];
        var fields = [];
        var sensitive = /password|secret|token|csrf|cnic|phone|mobile|email|address/i;

        Array.prototype.forEach.call(form.elements, function (field) {
            if (!field.name || field.disabled || sensitive.test(field.name) ||
                /^(hidden|submit|button|reset|password|file)$/i.test(field.type)) return;
            if (field.type === 'radio' && !field.checked) return;
            if (field.type === 'checkbox' && !field.checked) return;

            var value;
            if (field.tagName === 'SELECT') {
                value = Array.prototype.filter.call(field.options, function (option) {
                    return option.selected && option.value;
                }).map(function (option) {
                    return option.textContent.trim();
                }).join(', ');
            } else {
                value = (field.value || '').trim();
                if (/^(textarea|text|number|date|time|url|tel)$/i.test(field.type) &&
                    field.defaultValue === field.value) return;
            }
            if (!value) return;

            var label = fieldLabel(field);
            if (!label) return;
            fields.push({ label: label, value: value });
        });
        return fields;
    }

    function setOverview(form, details) {
        var section = dialog.querySelector('.axis-confirm-overview');
        var list = dialog.querySelector('.axis-confirm-details');
        list.replaceChildren();
        var overview = details || changedFieldDetails(form);
        if (!overview.length) {
            section.hidden = true;
            return;
        }
        overview.slice(0, 4).forEach(function (item) {
            var row = document.createElement('li');
            var label = document.createElement('span');
            var value = document.createElement('strong');
            label.textContent = item.label;
            value.textContent = item.value;
            row.append(label, value);
            list.appendChild(row);
        });
        if (overview.length > 4) {
            var more = document.createElement('li');
            more.className = 'axis-confirm-more';
            more.textContent = '+' + (overview.length - 4) + ' more field(s) included';
            list.appendChild(more);
        }
        section.hidden = false;
    }

    function confirmAction(message, options) {
        options = options || {};
        if (!dialog) dialog = createDialog();

        dialog.querySelector('#axisConfirmTitle').textContent = options.title || 'Please confirm';
        dialog.querySelector('.axis-confirm-message').textContent = message;
        setOverview(options.form, options.details);
        var accept = dialog.querySelector('.axis-confirm-accept');
        accept.querySelector('span').textContent = options.confirmLabel || 'Continue';
        accept.classList.toggle('is-danger', Boolean(options.danger));
        dialog.classList.toggle('is-danger', Boolean(options.danger));

        return new Promise(function (resolve) {
            var previouslyFocused = document.activeElement;
            function finish() {
                dialog.removeEventListener('close', finish);
                resolve(dialog.returnValue === 'confirm');
                if (previouslyFocused && typeof previouslyFocused.focus === 'function') {
                    previouslyFocused.focus();
                }
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
            danger: form.dataset.confirmDanger === 'true',
            form: form
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
