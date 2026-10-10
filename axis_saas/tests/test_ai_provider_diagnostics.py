import json
from io import BytesIO
from unittest import TestCase
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from django.test import override_settings

from axis_saas.views.ai.providers import (
    _provider_error_details,
    _safe_provider_error_value,
    run_assistant_model_turn,
)


class ProviderErrorDiagnosticsTests(TestCase):
    def test_extracts_structured_error_without_logging_credentials(self):
        error = Mock()
        error.read.return_value = json.dumps({
            'error': {
                'type': 'invalid_request_error',
                'code': 'unsupported_parameter',
                'message': 'Remove max_tokens. Leaked key gsk_abcdefghijklmnopqrstuvwxyz012345.',
            },
        }).encode()

        details = _provider_error_details(error)

        self.assertEqual(details['type'], 'invalid_request_error')
        self.assertEqual(details['code'], 'unsupported_parameter')
        self.assertIn('Remove max_tokens.', details['message'])
        self.assertNotIn('gsk_', details['message'])
        error.read.assert_called_once_with(4096)

    def test_error_text_is_collapsed_redacted_and_bounded(self):
        value = 'Provider says\nBearer sk-abcdefghijklmnopqrstuvwxyz and ' + ('x' * 500)

        result = _safe_provider_error_value(value, limit=64)

        self.assertEqual(len(result), 64)
        self.assertNotIn('sk-abcdefghijklmnopqrstuvwxyz', result)
        self.assertNotIn('\n', result)

    def test_non_json_error_body_has_no_details(self):
        error = Mock()
        error.read.return_value = b'<html>upstream error</html>'

        self.assertEqual(_provider_error_details(error), {})

    @override_settings(
        AI_ASSISTANT_API_KEY='test-key',
        AI_ASSISTANT_MODEL='openai/gpt-oss-120b',
    )
    @patch(
        'axis_saas.views.ai.providers.urlopen',
        side_effect=HTTPError(
            'https://provider.invalid/chat/completions',
            503,
            'Service Unavailable',
            {'x-request-id': 'request-123'},
            BytesIO(json.dumps({
                'error': {
                    'type': 'server_error',
                    'code': 'overloaded',
                    'message': 'Please retry; token gsk_abcdefghijklmnopqrstuvwxyz012345.',
                },
            }).encode()),
        ),
    )
    def test_http_log_has_provider_diagnostics_but_redacts_keys(self, _urlopen):
        with self.assertLogs('axis_saas.views.ai.providers', level='WARNING') as logs:
            result = run_assistant_model_turn(
                'Question',
                'Dashboard',
                [],
                tenant=None,
                schema_name='',
            )

        self.assertEqual(result['provider_status'], 'unavailable')
        output = '\n'.join(logs.output)
        self.assertIn('HTTP 503', output)
        self.assertIn('provider_type=server_error', output)
        self.assertIn('provider_code=overloaded', output)
        self.assertIn('request-123', output)
        self.assertIn('[redacted]', output)
        self.assertNotIn('gsk_', output)
