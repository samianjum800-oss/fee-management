"""Optional OpenAI-compatible provider for general AXIS help only."""

import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings

from .registry import execute_tool

logger = logging.getLogger(__name__)


def run_assistant_model_turn(
    message,
    current_page,
    available_pages,
    *,
    tenant,
    schema_name,
    roman_urdu=False,
    history=(),
):
    """Run a bounded assistant turn and execute only registered read tools."""
    api_key = getattr(settings, 'AI_ASSISTANT_API_KEY', '')
    model = getattr(settings, 'AI_ASSISTANT_MODEL', '')
    if not api_key or not model:
        return {'reply': None, 'actions': [], 'tools_used': []}

    page_context = '\n'.join(
        f"- {page['label']}: {page['description']} URL {page['url']}"
        for page in available_pages
    )
    from .knowledge import retrieve_documentation
    documentation = retrieve_documentation(message)
    docs_context = '\n\n'.join(
        f"[{section['source']} · {section['title']}]\n{section['text']}"
        for section in documentation
    )
    allow_school_data = getattr(settings, 'AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER', False)
    allow_school_data = allow_school_data and tenant is not None and tenant.is_feature_enabled(
        'ai_assistant_data_sharing', 'desktop'
    )
    tools = []
    if allow_school_data:
        from .registry import enabled_tool_definitions
        tools = enabled_tool_definitions(tenant)

    system_message = (
        'You are the AXIS school administrator copilot. Understand informal language, spelling mistakes, and multilingual questions. '
        'For Urdu or Hindi questions, answer in Roman Urdu using Latin letters. For English questions, answer in English. '
        'Use the supplied current page, enabled page catalogue, and documentation snippets to explain exactly where features are and what they do. '
        'Never invent a route, feature, metric, or school fact. If documentation is insufficient, say what is unknown. '
        'You may call only the supplied read-only tools. Never claim to write, approve, delete, collect, or modify records. '
        'When tools return action URLs, summarize the result briefly; the application will render the verified links separately. '
        f'Current page: {current_page}\nEnabled pages:\n{page_context}\n'
        f'Relevant AXIS documentation:\n{docs_context or "No matching documentation section."}'
    )
    endpoint = getattr(settings, 'AI_ASSISTANT_BASE_URL', 'https://api.openai.com/v1').rstrip('/')
    messages = [{'role': 'system', 'content': system_message}]
    for item in list(history)[-8:]:
        if not isinstance(item, dict) or item.get('role') not in ('user', 'assistant'):
            continue
        content = item.get('content')
        if isinstance(content, str) and content.strip():
            messages.append({'role': item['role'], 'content': content[:1000]})
    messages.append({'role': 'user', 'content': message[:500]})
    tools_used = []
    final_actions = []

    for _round in range(3):
        payload = {
            'model': model,
            'temperature': 0.2,
            'max_tokens': 700,
            'messages': messages,
        }
        if tools:
            payload['tools'] = tools
            payload['tool_choice'] = 'auto'
        request = Request(
            f'{endpoint}/chat/completions',
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        try:
            with urlopen(request, timeout=18) as response:
                result = json.loads(response.read(1024 * 1024).decode('utf-8'))
            assistant_message = result['choices'][0]['message']
            tool_calls = assistant_message.get('tool_calls') or []
            if not tool_calls:
                answer = (assistant_message.get('content') or '').strip()
                return {
                    'reply': answer[:4000] or None,
                    'actions': final_actions,
                    'tools_used': tools_used,
                }

            messages.append(assistant_message)
            for tool_call in tool_calls[:4]:
                function = tool_call.get('function') or {}
                tool_name = function.get('name', '')
                try:
                    result_data = execute_tool(
                        tool_name,
                        function.get('arguments', '{}'),
                        tenant=tenant,
                        schema_name=schema_name,
                        roman_urdu=roman_urdu,
                        pages=available_pages,
                    )
                    tools_used.append(tool_name)
                    final_actions.extend(result_data.get('actions', []))
                except (ValueError, PermissionError) as exc:
                    result_data = {'error': str(exc)}
                messages.append({
                    'role': 'tool',
                    'tool_call_id': tool_call.get('id', ''),
                    'content': json.dumps(result_data, ensure_ascii=False)[:12000],
                })
        except (HTTPError, URLError, TimeoutError, ValueError, KeyError, IndexError) as exc:
            logger.warning('AI assistant provider request failed: %s', type(exc).__name__)
            return {'reply': None, 'actions': [], 'tools_used': tools_used}

    return {
        'reply': 'I found the relevant school data, but could not finish summarizing it. The verified results are linked below.' if not roman_urdu else 'Relevant school data mil gaya, lekin summary complete nahin ho saki. Verified results neeche links mein hain.',
        'actions': final_actions,
        'tools_used': tools_used,
    }


def answer_general_question(message, current_page, available_pages):
    """Backward-compatible provider entry point for general help tests."""
    result = run_assistant_model_turn(
        message,
        current_page,
        available_pages,
        tenant=None,
        schema_name='',
    )
    return result['reply']
