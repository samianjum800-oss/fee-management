"""Authenticated assistant endpoint for a single school tenant."""

import json
import re

from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from ..helpers import get_tenant, require_tenant_type
from .intents import (
    extract_student_name_lookup,
    find_page_intent,
    is_roman_urdu,
    is_navigation_request,
    is_school_data_question,
    is_student_count_question,
)
from .knowledge import available_pages
from .providers import answer_general_question
from .tools import count_students, lookup_students


def _rate_limited(request, schema_name):
    session_key = request.session.session_key or 'no-session'
    key = f'ai_assistant_rate:{schema_name}:{session_key}'
    try:
        count = cache.get(key, 0)
        if count >= 30:
            return True
        cache.set(key, count + 1, timeout=60)
    except Exception:
        return False
    return False


def _current_page(path, pages):
    for page in pages:
        if path == page['url'] or path.startswith(page['url'].rstrip('/') + '/'):
            return page['label']
    return 'AXIS school admin'


@require_POST
@require_tenant_type(['school'])
def assistant_api(request, schema_name):
    if _rate_limited(request, schema_name):
        return JsonResponse({'error': 'Please wait a moment before sending another question.'}, status=429)

    try:
        payload = json.loads(request.body or b'{}')
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid request body.'}, status=400)
    message = payload.get('message', '') if isinstance(payload, dict) else ''
    if not isinstance(message, str):
        return JsonResponse({'error': 'Message must be text.'}, status=400)
    message = re.sub(r'\s+', ' ', message).strip()
    if not message or len(message) > 500:
        return JsonResponse({'error': 'Write a question up to 500 characters.'}, status=400)

    roman_urdu = is_roman_urdu(message)
    tenant = getattr(request, 'tenant', None) or get_tenant(request, schema_name)
    if not tenant.is_feature_enabled('ai_assistant', 'desktop'):
        return JsonResponse({'error': 'AI assistant is not enabled for this school.'}, status=404)

    pages = available_pages(tenant, schema_name)
    student_name = extract_student_name_lookup(message)
    if student_name:
        result = lookup_students(schema_name, student_name, roman_urdu=roman_urdu)
        result['kind'] = 'student_lookup'
        return JsonResponse(result)

    if is_student_count_question(message):
        result = count_students(schema_name, roman_urdu=roman_urdu)
        result['kind'] = 'student_count'
        return JsonResponse(result)

    page = find_page_intent(message, pages)
    if page and is_navigation_request(message):
        if roman_urdu:
            reply = f"{page['description']} Is page ko yahan khol sakte hain."
        else:
            reply = f"{page['description']} Open this page here."
        return JsonResponse({
            'kind': 'navigation',
            'reply': reply,
            'actions': [{'label': page['label'], 'detail': page['description'], 'url': page['url']}],
        })

    if is_school_data_question(message):
        if roman_urdu:
            reply = 'Private school records ke liye is assistant ka local search abhi sirf student names aur total student count support karta hai. Is sawal ka data kisi external AI ko nahin bheja gaya.'
        else:
            reply = 'Local search currently supports student names and total student counts. This school-data question was not sent to an external AI provider.'
        return JsonResponse({'kind': 'local_only', 'reply': reply, 'actions': []})

    if page:
        reply = page['description']
        return JsonResponse({
            'kind': 'page_help',
            'reply': reply,
            'actions': [{'label': page['label'], 'detail': page['description'], 'url': page['url']}],
        })

    current_page = _current_page(request.path, pages)
    answer = answer_general_question(message, current_page, pages)
    if answer:
        return JsonResponse({'kind': 'help', 'reply': answer, 'actions': []})

    if roman_urdu:
        reply = 'Is sawal ke liye general AI provider configure nahin hai. Main students dhoond sakta hoon ya enabled admin pages kholne ke links de sakta hoon.'
    else:
        reply = 'General AI is not configured yet. I can search students locally or link to enabled admin pages.'
    return JsonResponse({
        'kind': 'help',
        'reply': reply,
        'actions': [],
        'provider_configured': False,
    })
