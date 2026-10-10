import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.conf import settings
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.template.loader import get_template

from axis_saas.admin import SchoolClientForm
from axis_saas.views.ai.intents import (
    extract_student_name_lookup,
    extract_staff_name_lookup,
    extract_fee_balance_student,
    find_page_intent,
    is_roman_urdu,
    is_attendance_summary_question,
    is_school_data_question,
    is_student_count_question,
)
from axis_saas.views.ai.knowledge import available_pages
from axis_saas.views.ai.providers import answer_general_question, run_assistant_model_turn
from axis_saas.views.ai.knowledge import fuzzy_page_intent
from axis_saas.views.ai.registry import enabled_tool_definitions, execute_tool
from axis_saas.views.ai.tools import _fuzzy_student_names
from axis_saas.views.ai.assistant import assistant_api


class AssistantTestSession(dict):
    session_key = 'assistant-test'
    modified = False


class AssistantIntentTests(SimpleTestCase):
    def test_student_name_lookup_understands_roman_urdu_and_english(self):
        self.assertEqual(
            extract_student_name_lookup('Sami name ke kitne students hain?'),
            'sami',
        )
        self.assertEqual(
            extract_student_name_lookup('How many students named Sami?'),
            'sami',
        )
        self.assertEqual(extract_staff_name_lookup('Find teacher Sami Khan'), 'sami khan')
        self.assertEqual(extract_fee_balance_student('Sami ki pending fee kitni hai?'), 'sami')
        self.assertEqual(extract_student_name_lookup('Show students named Sami Khan'), 'sami khan')
        self.assertEqual(extract_student_name_lookup('Sami ka profile kholo'), 'sami')
        self.assertTrue(is_attendance_summary_question('Aaj attendance kaisi hai?'))
        self.assertFalse(is_attendance_summary_question('Attendance report kholo'))
        self.assertTrue(is_roman_urdu('Sami ke kitne students he?'))
        self.assertFalse(is_roman_urdu('How many students named Sami?'))

    def test_aggregate_count_does_not_misclassify_attendance_breakdown(self):
        self.assertTrue(is_student_count_question('Kitne students hain?'))
        self.assertTrue(is_student_count_question('Total students'))
        self.assertFalse(is_student_count_question('How many students were absent?'))
        self.assertFalse(is_student_count_question('Kitne students class 5 mein hain?'))

    def test_school_record_questions_are_local_only(self):
        self.assertTrue(is_school_data_question('Sami name ke kitne students hain?'))
        self.assertTrue(is_school_data_question('How much fee is pending?'))
        self.assertTrue(is_school_data_question('How many students were absent?'))
        self.assertFalse(is_school_data_question('What does attendance management do?'))
        self.assertFalse(is_school_data_question('How do I navigate the dashboard?'))

    def test_page_lookup_uses_enabled_tenant_features_only(self):
        enabled = {'students', 'reports'}
        tenant = SimpleNamespace(
            is_feature_enabled=lambda feature, channel: feature in enabled,
        )
        pages = available_pages(tenant, 'demo')
        page = find_page_intent('attendance report kholo', pages)
        self.assertIsNone(page)
        page = find_page_intent('student list kholo', pages)
        self.assertEqual(page['key'], 'students')
        self.assertTrue(page['url'].startswith('/portal/demo/'))
        typo_page = fuzzy_page_intent('defaultr kholo', pages)
        self.assertIsNone(typo_page)

    def test_fuzzy_page_matching_respects_enabled_page_catalog(self):
        enabled = {'defaulters'}
        tenant = SimpleNamespace(
            is_feature_enabled=lambda feature, channel: feature in enabled,
        )
        pages = available_pages(tenant, 'demo')
        self.assertEqual(fuzzy_page_intent('defaultr kholo', pages)['key'], 'defaulters')

    @patch('axis_saas.views.ai.tools.schema_context')
    @patch('axis_saas.views.ai.tools.Student.objects')
    def test_student_spelling_fallback_is_bounded_to_same_tenant(self, manager, tenant_context):
        names_query = Mock()
        names_query.exclude.return_value.values_list.return_value.distinct.return_value = [
            'Sami Khan', 'Ayesha Noor', 'Bilal Ahmed',
        ]
        manager.filter.return_value = names_query
        self.assertEqual(_fuzzy_student_names('demo', 'Samy Kahn', 5), ['Sami Khan'])
        tenant_context.assert_called_once_with('demo')


class AssistantConfigurationTests(SimpleTestCase):
    def test_admin_feature_is_desktop_opt_in(self):
        form = SchoolClientForm()
        self.assertIn(('ai_assistant', 'AI Assistant'), list(form.fields['desktop_features'].choices))
        self.assertIn(
            ('ai_assistant_data_sharing', 'AI Assistant: allow provider to process school records'),
            list(form.fields['desktop_features'].choices),
        )
        self.assertNotIn('ai_assistant', form.fields['desktop_features'].initial)
        self.assertNotIn('ai_assistant_data_sharing', form.fields['desktop_features'].initial)
        self.assertFalse(any(
            key == 'ai_assistant' for key, _label in form.fields['mobile_features'].choices
        ))

    @override_settings(AI_ASSISTANT_API_KEY='', AI_ASSISTANT_MODEL='')
    def test_general_provider_is_optional(self):
        self.assertIsNone(answer_general_question('How does AXIS work?', 'Dashboard', []))

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

    @override_settings(
        AI_ASSISTANT_API_KEY='test-key',
        AI_ASSISTANT_MODEL='test-model',
        AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER=False,
    )
    @patch('axis_saas.views.ai.providers.urlopen')
    def test_provider_receives_no_school_tools_without_consent(self, urlopen):
        urlopen.return_value = self._provider_response({
            'choices': [{'message': {'content': 'General help answer'}}],
        })
        tenant = SimpleNamespace(is_feature_enabled=lambda feature, _channel: feature == 'students')
        result = run_assistant_model_turn(
            'How does the student module work?',
            'Dashboard',
            [],
            tenant=tenant,
            schema_name='demo',
        )
        sent = json.loads(urlopen.call_args.args[0].data)
        self.assertNotIn('tools', sent)
        self.assertEqual(result['reply'], 'General help answer')

    @override_settings(
        AI_ASSISTANT_API_KEY='test-key',
        AI_ASSISTANT_MODEL='test-model',
        AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER=True,
    )
    @patch('axis_saas.views.ai.providers.execute_tool')
    @patch('axis_saas.views.ai.providers.urlopen')
    def test_consented_model_can_call_only_registered_tools(self, urlopen, execute_tool):
        urlopen.side_effect = [
            self._provider_response({'choices': [{'message': {
                'role': 'assistant',
                'content': None,
                'tool_calls': [{
                    'id': 'call-1',
                    'type': 'function',
                    'function': {'name': 'search_students', 'arguments': '{"query":"Sami"}'},
                }],
            }}]}),
            self._provider_response({'choices': [{'message': {'content': 'One student found.'}}]}),
        ]
        execute_tool.return_value = {
            'reply': 'Found one student.',
            'actions': [{'label': 'Sami · 1', 'url': '/portal/demo/students/1/'}],
        }
        tenant = SimpleNamespace(
            is_feature_enabled=lambda feature, _channel: feature in {
                'students', 'attendance_management', 'ai_assistant_data_sharing',
            },
        )
        result = run_assistant_model_turn(
            'Find Sami',
            'Students',
            [{'key': 'students', 'label': 'Students', 'description': 'Student records', 'url': '/portal/demo/students/'}],
            tenant=tenant,
            schema_name='demo',
        )
        first_payload = json.loads(urlopen.call_args_list[0].args[0].data)
        exposed_tools = {item['function']['name'] for item in first_payload['tools']}
        self.assertEqual(exposed_tools, {'search_students', 'count_students', 'attendance_today'})
        self.assertEqual(urlopen.call_count, 2)
        self.assertEqual(result['tools_used'], ['search_students'])
        self.assertEqual(result['actions'][0]['url'], '/portal/demo/students/1/')
        tool_messages = json.loads(urlopen.call_args_list[1].args[0].data)['messages']
        self.assertTrue(any(item['role'] == 'tool' for item in tool_messages))

    def _request(self, message, path='/portal/demo/reports/', current_path=None):
        body = {'message': message}
        if current_path is not None:
            body['current_path'] = current_path
        request = RequestFactory().post(
            path,
            data=json.dumps(body),
            content_type='application/json',
        )
        request.tenant = SimpleNamespace(
            tenant_type='wing_school',
            is_feature_enabled=lambda _feature, _channel: True,
        )
        request.session = AssistantTestSession()
        return request

    @patch('axis_saas.views.ai.assistant.run_assistant_model_turn')
    def test_private_school_data_question_stays_local(self, provider):
        response = assistant_api(
            self._request('How many students were absent this week?'),
            'demo',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['kind'], 'local_only')
        provider.assert_not_called()

    @patch('axis_saas.views.ai.assistant.lookup_students')
    def test_disabled_tenant_feature_blocks_student_lookup(self, student_lookup):
        request = self._request('Sami name ke kitne students hain?')
        request.tenant.is_feature_enabled = lambda _feature, _channel: False
        response = assistant_api(request, 'demo')
        self.assertEqual(response.status_code, 404)
        self.assertIn('not enabled', json.loads(response.content)['error'])
        student_lookup.assert_not_called()

    @patch('axis_saas.views.ai.assistant.run_assistant_model_turn', return_value={'reply': 'Help answer', 'actions': [], 'tools_used': []})
    def test_provider_context_uses_server_path_not_client_path(self, provider):
        response = assistant_api(
            self._request(
                'How do I use this page?',
                current_path='/portal/demo/fee/collection/',
            ),
            'demo',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(provider.call_args.args[1], 'Fee collection')

    @patch('axis_saas.views.ai.assistant.run_assistant_model_turn', return_value={'reply': 'Help answer', 'actions': [], 'tools_used': []})
    def test_revoked_data_consent_purges_provider_history(self, provider):
        request = self._request('How does the assistant work?')
        history_key = 'ai_assistant_history:demo'
        request.session[history_key] = [
            {'role': 'assistant', 'content': 'A previous private student result.'},
        ]
        response = assistant_api(request, 'demo')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(provider.call_args.kwargs['history'], [])
        self.assertNotIn(history_key, request.session)

    @override_settings(AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER=True)
    def test_tool_registry_is_feature_scoped_and_unknown_tools_are_rejected(self):
        tenant = SimpleNamespace(
            is_feature_enabled=lambda feature, channel: feature in {
                'students', 'reports', 'ai_assistant_data_sharing',
            },
        )
        definitions = enabled_tool_definitions(tenant)
        names = {item['function']['name'] for item in definitions}
        self.assertIn('search_students', names)
        self.assertNotIn('search_staff', names)
        with self.assertRaises(ValueError):
            execute_tool('delete_everything', '{}', tenant=tenant, schema_name='demo')

    @override_settings(AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER=True)
    def test_school_data_tools_require_tenant_opt_in(self):
        tenant = SimpleNamespace(
            is_feature_enabled=lambda feature, _channel: feature in {'students', 'ai_assistant'},
        )
        self.assertEqual(enabled_tool_definitions(tenant), [])

    def test_widget_template_compiles(self):
        self.assertIsNotNone(get_template('tenant/ai/widget.html'))

    def test_shared_admin_header_always_mounts_assistant_launcher(self):
        base_template = Path(settings.BASE_DIR, 'templates', 'tenant', 'base.html').read_text()
        self.assertIn('id="axis-ai-header-trigger"', base_template)
        self.assertIn("{% include 'tenant/ai/widget.html' %}", base_template)
