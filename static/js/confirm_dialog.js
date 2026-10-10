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

    function fieldValue(field, useDefault) {
        if (field.tagName === 'SELECT') {
            return Array.prototype.filter.call(field.options, function (option) {
                return useDefault ? option.defaultSelected : option.selected;
            }).filter(function (option) {
                return option.value;
            }).map(function (option) {
                return option.textContent.trim();
            }).join(', ');
        }
        if (field.type === 'checkbox' || field.type === 'radio') {
            return (useDefault ? field.defaultChecked : field.checked) ?
                (field.value || 'Selected') : 'Not selected';
        }
        return useDefault ? field.defaultValue : field.value;
    }

    function isExistingRecord(form) {
        if (form.dataset.confirmExisting === 'true' || form.dataset.confirmMode === 'edit') return true;
        if (form.dataset.confirmExisting === 'false' || form.dataset.confirmMode === 'create') return false;
        if (/\/edit(?:\/|$)/i.test(form.action)) return true;
        return Array.prototype.some.call(form.elements, function (field) {
            return /^(class|subject|assignment|category|product|staff|student)_?id$/i.test(field.name) &&
                field.type === 'hidden' && Boolean(field.value);
        });
    }

    function changedFieldDetails(form) {
        if (!form) return [];
        var fields = [];
        var existing = isExistingRecord(form);
        var originals = JSON.parse(form.dataset.confirmOriginals || '{}');
        var sensitive = /password|secret|token|csrf/i;

        Array.prototype.forEach.call(form.elements, function (field) {
            if (!field.name || field.disabled || sensitive.test(field.name) ||
                /^(hidden|submit|button|reset|password|file)$/i.test(field.type)) return;
            if (field.type === 'radio' && !field.checked) return;
            if (field.type === 'checkbox' && !field.checked) return;

            var value = String(fieldValue(field, false) || '').trim();
            var original = Object.prototype.hasOwnProperty.call(originals, field.name) ?
                String(originals[field.name]) : String(fieldValue(field, true) || '').trim();
            if (existing && value === original) return;
            if (!existing && !value) return;

            var label = fieldLabel(field);
            if (!label) return;
            fields.push({
                label: label,
                value: existing ? (original || 'Not set') + '  →  ' + (value || 'Not set') : value,
                previous: existing ? (original || 'Not set') : null,
                current: value || 'Not set'
            });
        });
        return fields;
    }

    function setOverview(form, details, existingOverride) {
        var section = dialog.querySelector('.axis-confirm-overview');
        var list = dialog.querySelector('.axis-confirm-details');
        list.replaceChildren();
        var existing = existingOverride === undefined ?
            (form ? isExistingRecord(form) : false) : existingOverride;
        var overview = details || changedFieldDetails(form);
        if (!overview.length) {
            var message = dialog.querySelector('.axis-confirm-message');
            if (existing) {
                message.textContent += ' No field changes were detected.';
            }
            section.hidden = true;
            return;
        }
        overview.forEach(function (item) {
            var row = document.createElement('li');
            var label = document.createElement('span');
            var value = document.createElement('strong');
            label.textContent = item.label;
            if (item.previous !== null && item.previous !== undefined) {
                var before = document.createElement('span');
                before.className = 'axis-confirm-before';
                before.textContent = item.previous || 'Not set';
                var after = document.createElement('span');
                after.className = 'axis-confirm-after';
                after.textContent = item.current;
                value.append(before, document.createTextNode(' → '), after);
            } else {
                value.textContent = item.value;
            }
            row.append(label, value);
            list.appendChild(row);
        });
        section.hidden = false;
    }

    window.axisCaptureConfirmOriginals = function (form) {
        if (!(form instanceof HTMLFormElement)) return;
        var originals = {};
        Array.prototype.forEach.call(form.elements, function (field) {
            if (field.name && field.type !== 'hidden' && field.type !== 'password' &&
                field.type !== 'file' && field.type !== 'submit' && field.type !== 'button') {
                originals[field.name] = String(fieldValue(field, false) || '');
            }
        });
        form.dataset.confirmOriginals = JSON.stringify(originals);
    };

    function confirmAction(message, options) {
        options = options || {};
        if (!dialog) dialog = createDialog();

        dialog.querySelector('#axisConfirmTitle').textContent = options.title || 'Please confirm';
        dialog.querySelector('.axis-confirm-message').textContent = message;
        dialog.dataset.confirmExisting = options.form && isExistingRecord(options.form) ? 'true' : 'false';
        setOverview(options.form, options.details, options.existing);
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
