(function () {
    const launcher = document.getElementById('axis-ai-launcher');
    const headerTrigger = document.getElementById('axis-ai-header-trigger');
    const panel = document.getElementById('axis-ai-panel');
    if (!launcher || !panel) return;

    const closeButton = document.getElementById('axis-ai-close');
    const form = document.getElementById('axis-ai-form');
    const input = document.getElementById('axis-ai-input');
    const sendButton = document.getElementById('axis-ai-send');
    const messages = document.getElementById('axis-ai-messages');
    const endpoint = panel.dataset.endpoint;
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
    let previousFocus = null;

    function setOpen(open) {
        panel.setAttribute('aria-hidden', String(!open));
        launcher.setAttribute('aria-expanded', String(open));
        if (headerTrigger) headerTrigger.setAttribute('aria-expanded', String(open));
        if (open) {
            previousFocus = document.activeElement;
            input.focus();
        } else if (previousFocus && typeof previousFocus.focus === 'function') {
            previousFocus.focus();
        }
    }

    function appendMessage(text, role, actions) {
        const wrapper = document.createElement('div');
        wrapper.className = 'axis-ai-message' + (role === 'user' ? ' user' : '');
        wrapper.textContent = text;
        if (Array.isArray(actions) && actions.length) {
            const actionList = document.createElement('div');
            actionList.className = 'axis-ai-actions';
            actions.forEach(function (action) {
                if (!action || typeof action.url !== 'string' || !action.url.startsWith('/')) return;
                const link = document.createElement('a');
                link.href = action.url;
                const label = document.createElement('span');
                label.textContent = action.label || 'Open';
                link.appendChild(label);
                if (action.detail) {
                    const detail = document.createElement('small');
                    detail.textContent = action.detail;
                    link.appendChild(detail);
                }
                actionList.appendChild(link);
            });
            wrapper.appendChild(actionList);
        }
        messages.appendChild(wrapper);
        messages.scrollTop = messages.scrollHeight;
        return wrapper;
    }

    async function sendMessage(message) {
        const question = (message || '').trim();
        if (!question || sendButton.disabled) return;
        appendMessage(question, 'user');
        input.value = '';
        sendButton.disabled = true;
        sendButton.textContent = '…';
        const pending = appendMessage('Soch raha hoon…', 'assistant');
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ message: question, current_path: panel.dataset.currentPath })
            });
            const result = await response.json();
            pending.remove();
            if (!response.ok) {
                appendMessage(result.error || 'Assistant request complete nahin kar saka. Dobara try karein.', 'assistant');
            } else {
                appendMessage(result.reply || 'Is sawal ka jawab nahin mila.', 'assistant', result.actions);
            }
        } catch (error) {
            pending.remove();
            appendMessage('Connection nahin ho saka. Internet ya server check karke dobara try karein.', 'assistant');
        } finally {
            sendButton.disabled = false;
            sendButton.textContent = 'Send';
            input.focus();
        }
    }

    [launcher, headerTrigger].filter(Boolean).forEach(function (trigger) {
        trigger.addEventListener('click', function () {
            setOpen(panel.getAttribute('aria-hidden') === 'true');
        });
    });
    closeButton.addEventListener('click', function () { setOpen(false); });
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && panel.getAttribute('aria-hidden') === 'false') setOpen(false);
    });
    form.addEventListener('submit', function (event) {
        event.preventDefault();
        sendMessage(input.value);
    });
    document.querySelectorAll('[data-ai-prompt]').forEach(function (button) {
        button.addEventListener('click', function () { sendMessage(button.dataset.aiPrompt); });
    });
}());
