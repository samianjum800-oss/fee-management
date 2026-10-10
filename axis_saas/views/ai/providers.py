"""Optional OpenAI-compatible provider for general AXIS help only."""

import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings

logger = logging.getLogger(__name__)


def answer_general_question(message, current_page, available_pages):
    """Answer general product questions without attaching school records.

    Student lookups and other data tools are handled locally and never passed
    to this provider. The configured provider receives the user's general
    question and the public page catalogue only.
    """
    api_key = getattr(settings, 'AI_ASSISTANT_API_KEY', '')
    model = getattr(settings, 'AI_ASSISTANT_MODEL', '')
    if not api_key or not model:
        return None

    page_context = '\n'.join(
        f"- {page['label']}: {page['description']} URL {page['url']}"
        for page in available_pages
    )
    system_message = (
        'You are AXIS school administration help. Explain existing features using only the supplied page catalogue. '
        'Do not claim you can modify records, approve requests, collect fees, or execute actions. '
        'When the user writes Urdu or Hindi, reply in Roman Urdu using Latin letters. For English questions, reply in English. '
        'If the page catalogue does not support an answer, say so clearly. Never invent tenant data. '
        f'Current page: {current_page}\nAvailable pages:\n{page_context}'
    )
    endpoint = getattr(settings, 'AI_ASSISTANT_BASE_URL', 'https://api.openai.com/v1').rstrip('/')
    payload = json.dumps({
        'model': model,
        'temperature': 0.2,
        'messages': [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': message[:500]},
        ],
    }).encode('utf-8')
    request = Request(
        f'{endpoint}/chat/completions',
        data=payload,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with urlopen(request, timeout=12) as response:
            result = json.loads(response.read(1024 * 1024).decode('utf-8'))
        answer = result['choices'][0]['message']['content'].strip()
        return answer[:4000] if answer else None
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError, IndexError) as exc:
        logger.warning('AI assistant provider request failed: %s', type(exc).__name__)
        return None
