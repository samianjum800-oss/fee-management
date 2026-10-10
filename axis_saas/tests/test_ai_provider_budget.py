import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from axis_saas.views.ai.query import DATASETS
from axis_saas.views.ai.providers import run_assistant_model_turn
from axis_saas.views.ai.registry import enabled_tool_definitions
from axis_saas.views.ai.providers import run_assistant_model_turn


class ProviderToolBudgetTests(SimpleTestCase):
    @staticmethod
    def _provider_response(body):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, _limit):
                return json.dumps(body).encode()

        return Response()

    def _query_schema(self, question):
        tenant = SimpleNamespace(is_feature_enabled=lambda _feature, _channel: True)
        tools = enabled_tool_definitions(
            tenant,
            consent_confirmed=True,
        )
        tool = next(
            item['function'] for item in tools
            if item['function']['name'] == 'query_school_data'
        )
        return tool

    @override_settings(AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER=True)
    def test_query_schema_keeps_all_enabled_datasets_with_compact_field_types(self):
        tool = self._query_schema('How many active students are in grade 10?')
        properties = tool['parameters']['properties']

        self.assertEqual(set(properties['dataset']['enum']), set(DATASETS))
        self.assertEqual(properties['filters']['items']['properties']['field']['type'], 'string')
        self.assertEqual(properties['group_by']['type'], 'string')
        self.assertEqual(properties['fields']['items']['type'], 'string')
        self.assertEqual(properties['limit']['maximum'], 10)
        self.assertNotIn('enum', properties['fields']['items'])
        self.assertLess(len(json.dumps(tool)), 12000)
        self.assertIn('parent_mobile', tool['description'])

    @override_settings(AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER=True)
    def test_fee_by_class_schema_still_exposes_fee_and_class_datasets(self):
        tool = self._query_schema('How much pending fee for class 10 section A?')
        datasets = set(tool['parameters']['properties']['dataset']['enum'])

        self.assertIn('fee_records', datasets)
        self.assertIn('classes', datasets)

    @override_settings(AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER=True)
    def test_parent_student_fields_remain_available_in_compact_catalog(self):
        tool = self._query_schema('Which student has father name Hazir Khan?')

        self.assertIn('students', tool['parameters']['properties']['dataset']['enum'])
        self.assertIn('parent_mobile', tool['description'])

    @override_settings(
        AI_ASSISTANT_API_KEY='test-key',
        AI_ASSISTANT_MODEL='openai/gpt-oss-120b',
        AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER=True,
    )
    @patch('axis_saas.views.ai.providers.urlopen')
    def test_gpt_oss_request_keeps_all_datasets_under_payload_budget(self, urlopen):
        urlopen.return_value = self._provider_response({
            'choices': [{'message': {'content': 'There are 12 students.'}}],
        })
        tenant = SimpleNamespace(is_feature_enabled=lambda _feature, _channel: True)
        run_assistant_model_turn(
            'How many students are active?',
            'Dashboard',
            [],
            tenant=tenant,
            schema_name='demo',
            provider_data_consent=True,
        )

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data)
        query_schema = next(
            item['function'] for item in payload['tools']
            if item['function']['name'] == 'query_school_data'
        )
        self.assertEqual(payload['max_completion_tokens'], 1536)
        self.assertEqual(payload['reasoning_effort'], 'low')
        self.assertEqual(payload['reasoning_format'], 'hidden')
        self.assertFalse(payload['parallel_tool_calls'])
        self.assertEqual(len(payload['tools']), 1)
        self.assertEqual(
            set(query_schema['parameters']['properties']['dataset']['enum']),
            set(DATASETS),
        )
        self.assertLess(len(request.data), 20000)

    @override_settings(
        AI_ASSISTANT_API_KEY='test-key',
        AI_ASSISTANT_MODEL='openai/gpt-oss-120b',
        AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER=True,
    )
    @patch('axis_saas.views.ai.providers.execute_tool')
    @patch('axis_saas.views.ai.providers.urlopen')
    def test_followup_after_data_tool_uses_smaller_budget(self, urlopen, execute_tool):
        def response(body):
            class FakeResponse:
                def __enter__(self):
                    return self

                def __exit__(self, *_args):
                    return False

                def read(self, _limit):
                    return json.dumps(body).encode()

            return FakeResponse()

        urlopen.side_effect = [
            response({'choices': [{'message': {
                'role': 'assistant',
                'content': None,
                'tool_calls': [{
                    'id': 'query-1',
                    'type': 'function',
                    'function': {
                        'name': 'query_school_data',
                        'arguments': '{"dataset":"students","operation":"count"}',
                    },
                }],
            }}]}),
            response({'choices': [{'message': {'content': 'There are 12 students.'}}]}),
        ]
        execute_tool.return_value = {'dataset': 'students', 'operation': 'count', 'count': 12}
        tenant = SimpleNamespace(is_feature_enabled=lambda _feature, _channel: True)

        result = run_assistant_model_turn(
            'How many students are there?',
            'Dashboard',
            [],
            tenant=tenant,
            schema_name='demo',
            provider_data_consent=True,
        )

        self.assertEqual(result['reply'], 'There are 12 students.')
        first_payload = json.loads(urlopen.call_args_list[0].args[0].data)
        followup_payload = json.loads(urlopen.call_args_list[1].args[0].data)
        self.assertEqual(first_payload['max_completion_tokens'], 1536)
        self.assertEqual(followup_payload['max_completion_tokens'], 1024)
        self.assertTrue(any(item['role'] == 'tool' for item in followup_payload['messages']))
