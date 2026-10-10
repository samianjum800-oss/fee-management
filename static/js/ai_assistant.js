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
    const consentGate = document.getElementById('axis-ai-consent');
    const consentCheckbox = document.getElementById('axis-ai-consent-checkbox');
    const allowDataButton = document.getElementById('axis-ai-consent-allow');
    const privateModeButton = document.getElementById('axis-ai-consent-private');
    const endpoint = panel.dataset.endpoint;
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
    let previousFocus = null;
    let conversationId = null;
    let providerConsent = false;
    let chatStarted = false;

    function createConversationId() {
        if (window.crypto && typeof window.crypto.randomUUID === 'function') {
            return window.crypto.randomUUID();
        }
        const hex = Array.from({ length: 32 }, function () {
            return Math.floor(Math.random() * 16).toString(16);
        });
        hex[12] = '4';
        hex[16] = ['8', '9', 'a', 'b'][Math.floor(Math.random() * 4)];
        const value = hex.join('');
        return `${value.slice(0, 8)}-${value.slice(8, 12)}-${value.slice(12, 16)}-${value.slice(16, 20)}-${value.slice(20)}`;
    }

    function setChatEnabled(enabled) {
        input.disabled = !enabled;
        sendButton.disabled = !enabled;
        document.querySelectorAll('[data-ai-prompt]').forEach(function (button) {
            button.disabled = !enabled;
        });
    }

    function beginConversation() {
        conversationId = createConversationId();
        providerConsent = false;
        chatStarted = false;
        consentGate.hidden = false;
        if (consentCheckbox) consentCheckbox.checked = false;
        if (allowDataButton) allowDataButton.disabled = true;
        setChatEnabled(false);
    }

    function selectPrivacyMode(allowSchoolData) {
        providerConsent = allowSchoolData;
        chatStarted = true;
        consentGate.hidden = true;
        setChatEnabled(true);
        input.focus();
    }

    function endConversation() {
        const endedConversationId = conversationId;
        if (endedConversationId) {
            fetch(endpoint, {
                method: 'POST',
                credentials: 'same-origin',
                keepalive: true,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ action: 'end_chat', conversation_id: endedConversationId })
            }).catch(function () {});
        }
        conversationId = null;
        providerConsent = false;
        chatStarted = false;
        const welcome = messages.querySelector('[data-ai-welcome]');
        if (welcome) messages.replaceChildren(welcome);
        setChatEnabled(false);
    }

    function setOpen(open) {
        panel.setAttribute('aria-hidden', String(!open));
        launcher.setAttribute('aria-expanded', String(open));
        if (headerTrigger) headerTrigger.setAttribute('aria-expanded', String(open));
        if (open) {
            previousFocus = document.activeElement;
            if (!conversationId) beginConversation();
        } else if (previousFocus && typeof previousFocus.focus === 'function') {
            endConversation();
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
        if (!chatStarted || !question || sendButton.disabled) return;
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
                body: JSON.stringify({
                    message: question,
                    current_path: panel.dataset.currentPath,
                    conversation_id: conversationId,
                    confirm_school_data_sharing: providerConsent
                })
            });
            const result = await response.json();
            pending.remove();
            if (!response.ok) {
                appendMessage(result.reply || result.error || 'Assistant request complete nahin kar saka. Dobara try karein.', 'assistant');
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
    if (consentCheckbox && allowDataButton) {
        consentCheckbox.addEventListener('change', function () {
            allowDataButton.disabled = !consentCheckbox.checked;
        });
        allowDataButton.addEventListener('click', function () {
            if (consentCheckbox.checked) selectPrivacyMode(true);
        });
    }
    privateModeButton.addEventListener('click', function () { selectPrivacyMode(false); });
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
