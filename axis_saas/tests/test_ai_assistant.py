import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch
from urllib.error import URLError

from django.apps import apps
from django.conf import settings
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.template.loader import get_template

from axis_saas.admin import SchoolClientForm
from axis_saas.views.ai.intents import (
    extract_class_pending_fee,
    extract_student_name_lookup,
    extract_student_parent_lookup,
    extract_staff_name_lookup,
    extract_fee_balance_student,
    find_page_intent,
    is_roman_urdu,
    is_attendance_summary_question,
    is_school_data_question,
    is_student_count_question,
)
from axis_saas.views.ai.knowledge import (
    _VisibleTemplateText,
    available_pages,
    retrieve_documentation,
)
from axis_saas.views.ai.providers import run_assistant_model_turn
from axis_saas.views.ai.knowledge import fuzzy_page_intent
from axis_saas.views.ai.registry import enabled_tool_definitions, execute_tool
from axis_saas.views.ai.query import (
    DATASETS,
    _coerce_filter_value,
    _execute_school_data_query,
    _resolve_model_field,
    _validate_bounded_date_range,
    query_school_data,
)
from axis_saas.views.ai.tools import _fuzzy_student_names
from axis_saas.views.ai.assistant import _rate_limited, assistant_api


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
        self.assertEqual(
            extract_student_parent_lookup('Hazir Khan kis bache ka name he'),
            'hazir khan',
        )
        self.assertEqual(
            extract_class_pending_fee('10 A ki total pending fee kitni hai'),
            ('10', 'A'),
        )
        self.assertEqual(
            extract_class_pending_fee('10A ki total pending fee kitni hai'),
            ('10', 'A'),
        )
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
        self.assertTrue(is_school_data_question('How much sales revenue last month?'))
        self.assertTrue(is_school_data_question('Show me the timetable for class 5'))
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

    def test_local_knowledge_retrieves_visible_admin_page_copy(self):
        results = retrieve_documentation('financial reports transaction history', limit=10)
        self.assertTrue(any(
            item['source'] == 'templates/tenant/reports/overview.html'
            for item in results
        ))

    def test_template_indexer_ignores_scripts_and_styles(self):
        parser = _VisibleTemplateText()
        parser.feed(
            '<style>.secret { color: red; }</style>'
            '<script>fetch("/private-api");</script>'
            '<button title="Open report">Reports</button>'
        )
        visible = ' '.join(parser.parts)
        self.assertIn('Open report', visible)
        self.assertIn('Reports', visible)
        self.assertNotIn('secret', visible)
        self.assertNotIn('private-api', visible)

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
    @patch('axis_saas.views.ai.assistant.cache.incr', return_value=30)
    @patch('axis_saas.views.ai.assistant.cache.add', return_value=False)
    def test_rate_limit_allows_thirtieth_request(self, cache_add, cache_incr):
        request = SimpleNamespace(session=AssistantTestSession())
        self.assertFalse(_rate_limited(request, 'demo'))
        cache_add.assert_called_once_with('ai_assistant_rate:demo:assistant-test', 1, timeout=60)
        cache_incr.assert_called_once_with('ai_assistant_rate:demo:assistant-test')

    @patch('axis_saas.views.ai.assistant.cache.incr', return_value=31)
    @patch('axis_saas.views.ai.assistant.cache.add', return_value=False)
    def test_rate_limit_rejects_requests_after_thirty(self, _cache_add, _cache_incr):
        request = SimpleNamespace(session=AssistantTestSession())
        self.assertTrue(_rate_limited(request, 'demo'))

    @patch('axis_saas.views.ai.assistant.cache.add', side_effect=RuntimeError('cache unavailable'))
    def test_rate_limit_fails_closed_when_cache_is_unavailable(self, _cache_add):
        request = SimpleNamespace(session=AssistantTestSession())
        self.assertTrue(_rate_limited(request, 'demo'))

    def test_admin_feature_is_desktop_opt_in(self):
        form = SchoolClientForm()
        self.assertIn(('ai_assistant', 'AI Assistant'), list(form.fields['desktop_features'].choices))
        self.assertNotIn(
            'ai_assistant_data_sharing',
            [key for key, _label in form.fields['desktop_features'].choices],
        )
        self.assertNotIn('ai_assistant', form.fields['desktop_features'].initial)
        self.assertNotIn('ai_assistant_data_sharing', form.fields['desktop_features'].initial)
        self.assertFalse(any(
            key == 'ai_assistant' for key, _label in form.fields['mobile_features'].choices
        ))

    @override_settings(AI_ASSISTANT_API_KEY='', AI_ASSISTANT_MODEL='')
    def test_general_provider_is_optional(self):
        result = run_assistant_model_turn(
            'How does AXIS work?',
            'Dashboard',
            [],
            tenant=None,
            schema_name='',
        )
        self.assertIsNone(result['reply'])
        self.assertEqual(result['provider_status'], 'unconfigured')

    @override_settings(AI_ASSISTANT_API_KEY='test-key', AI_ASSISTANT_MODEL='test-model')
    @patch('axis_saas.views.ai.providers.urlopen', side_effect=URLError('provider unavailable'))
    def test_provider_connection_failure_is_reported_as_unavailable(self, _urlopen):
        result = run_assistant_model_turn(
            'How does AXIS work?',
            'Dashboard',
            [],
            tenant=None,
            schema_name='',
        )
        self.assertIsNone(result['reply'])
        self.assertEqual(result['provider_status'], 'unavailable')

    @override_settings(AI_ASSISTANT_API_KEY='test-key', AI_ASSISTANT_MODEL='test-model')
    @patch('axis_saas.views.ai.providers.urlopen')
    def test_empty_provider_response_is_reported_as_unavailable(self, urlopen):
        urlopen.return_value = self._provider_response({
            'choices': [{'message': {'content': ''}}],
        })
        result = run_assistant_model_turn(
            'How does AXIS work?',
            'Dashboard',
            [],
            tenant=None,
            schema_name='',
        )
        self.assertIsNone(result['reply'])
        self.assertEqual(result['provider_status'], 'unavailable')

    @override_settings(AI_ASSISTANT_API_KEY='test-key', AI_ASSISTANT_MODEL='test-model')
    @patch('axis_saas.views.ai.providers.urlopen')
    def test_malformed_provider_response_is_reported_as_unavailable(self, urlopen):
        urlopen.return_value = self._provider_response({'choices': [None]})
        result = run_assistant_model_turn(
            'How does AXIS work?',
            'Dashboard',
            [],
            tenant=None,
            schema_name='',
        )
        self.assertIsNone(result['reply'])
        self.assertEqual(result['provider_status'], 'unavailable')

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
        AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER=True,
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
        self.assertEqual(result['provider_status'], 'ready')

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
            provider_data_consent=True,
        )
        first_payload = json.loads(urlopen.call_args_list[0].args[0].data)
        exposed_tools = {item['function']['name'] for item in first_payload['tools']}
        self.assertEqual(exposed_tools, {
            'search_students', 'count_students', 'attendance_today', 'attendance_range',
        })
        self.assertEqual(urlopen.call_count, 2)
        self.assertEqual(result['tools_used'], ['search_students'])
        self.assertEqual(result['actions'][0]['url'], '/portal/demo/students/1/')
        tool_messages = json.loads(urlopen.call_args_list[1].args[0].data)['messages']
        self.assertTrue(any(item['role'] == 'tool' for item in tool_messages))

    @override_settings(
        AI_ASSISTANT_API_KEY='test-key',
        AI_ASSISTANT_MODEL='test-model',
        AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER=True,
    )
    @patch('axis_saas.views.ai.providers.execute_tool')
    @patch('axis_saas.views.ai.providers.urlopen')
    def test_model_can_route_natural_language_to_scoped_query_tool(self, urlopen, execute_tool):
        urlopen.side_effect = [
            self._provider_response({'choices': [{'message': {
                'role': 'assistant',
                'content': None,
                'tool_calls': [{
                    'id': 'query-call',
                    'type': 'function',
                    'function': {
                        'name': 'query_school_data',
                        'arguments': '{"dataset":"students","operation":"count","filters":[{"field":"grade","operator":"eq","value":"5"}]}',
                    },
                }],
            }}]}),
            self._provider_response({'choices': [{'message': {'content': 'There are 24 students in grade 5.'}}]}),
        ]
        execute_tool.return_value = {
            'dataset': 'students', 'operation': 'count', 'count': 24,
        }
        tenant = SimpleNamespace(
            is_feature_enabled=lambda feature, _channel: feature in {
                'ai_assistant', 'ai_assistant_data_sharing', 'students',
            },
        )
        result = run_assistant_model_turn(
            'How many students are in grade 5?',
            'Dashboard',
            [],
            tenant=tenant,
            schema_name='demo',
            provider_data_consent=True,
        )
        first_payload = json.loads(urlopen.call_args_list[0].args[0].data)
        query_schema = next(
            item['function'] for item in first_payload['tools']
            if item['function']['name'] == 'query_school_data'
        )
        self.assertEqual(
            query_schema['parameters']['properties']['dataset']['enum'],
            ['students'],
        )
        execute_tool.assert_called_once()
        self.assertEqual(execute_tool.call_args.args[0], 'query_school_data')
        self.assertEqual(result['tools_used'], ['query_school_data'])
        self.assertEqual(result['reply'], 'There are 24 students in grade 5.')

    def _request(
        self,
        message,
        path='/portal/demo/reports/',
        current_path=None,
        conversation_id=None,
        confirm_school_data_sharing=False,
        action=None,
    ):
        body = {'message': message}
        if action is not None:
            body['action'] = action
        if current_path is not None:
            body['current_path'] = current_path
        if conversation_id is not None:
            body['conversation_id'] = conversation_id
            body['confirm_school_data_sharing'] = confirm_school_data_sharing
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

    @patch('axis_saas.views.ai.assistant._rate_limited', return_value=False)
    @patch('axis_saas.views.ai.assistant.run_assistant_model_turn')
    def test_private_school_data_question_stays_local(self, provider, _rate_limited):
        response = assistant_api(
            self._request('How many students were absent this week?'),
            'demo',
        )
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertEqual(body['kind'], 'local_only')
        self.assertIn('platform data-sharing policy', body['reply'])
        self.assertIn('confirm at the start of each chat', body['reply'])
        provider.assert_not_called()

    @override_settings(
        AI_ASSISTANT_API_KEY='test-key',
        AI_ASSISTANT_MODEL='test-model',
        AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER=True,
    )
    @patch(
        'axis_saas.views.ai.assistant.run_assistant_model_turn',
        return_value={'reply': 'Verified answer', 'actions': [], 'tools_used': []},
    )
    @patch('axis_saas.views.ai.assistant._rate_limited', return_value=False)
    def test_chat_confirmation_is_recorded_and_passed_to_provider(
        self, _rate_limited, provider,
    ):
        conversation_id = '8f853ba6-68a4-4c86-9974-3bb9259076a4'
        request = self._request(
            'How does the school inventory work?',
            conversation_id=conversation_id,
            confirm_school_data_sharing=True,
        )
        response = assistant_api(request, 'demo')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            request.session['ai_assistant_consent:demo'], conversation_id,
        )
        self.assertTrue(provider.call_args.kwargs['provider_data_consent'])

    @override_settings(
        AI_ASSISTANT_API_KEY='test-key',
        AI_ASSISTANT_MODEL='test-model',
        AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER=True,
    )
    @patch(
        'axis_saas.views.ai.assistant.run_assistant_model_turn',
        return_value={'reply': 'Help answer', 'actions': [], 'tools_used': []},
    )
    @patch('axis_saas.views.ai.assistant._rate_limited', return_value=False)
    def test_chat_consent_does_not_transfer_to_another_conversation(
        self, _rate_limited, provider,
    ):
        request = self._request(
            'How does the school inventory work?',
            conversation_id='a5f03b4e-a04d-4f3f-92bf-c3980289ea01',
        )
        request.session['ai_assistant_consent:demo'] = '8f853ba6-68a4-4c86-9974-3bb9259076a4'
        response = assistant_api(request, 'demo')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(provider.call_args.kwargs['provider_data_consent'])

    @override_settings(
        AI_ASSISTANT_API_KEY='test-key',
        AI_ASSISTANT_MODEL='test-model',
        AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER=True,
    )
    @patch(
        'axis_saas.views.ai.assistant.run_assistant_model_turn',
        return_value={'reply': 'Help answer', 'actions': [], 'tools_used': []},
    )
    @patch('axis_saas.views.ai.assistant._rate_limited', return_value=False)
    def test_chat_consent_does_not_transfer_across_school_schemas(
        self, _rate_limited, provider,
    ):
        conversation_id = '8f853ba6-68a4-4c86-9974-3bb9259076a4'
        request = self._request(
            'How does the school inventory work?',
            path='/portal/other/reports/',
            conversation_id=conversation_id,
        )
        request.session['ai_assistant_consent:demo'] = conversation_id
        response = assistant_api(request, 'other')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(provider.call_args.kwargs['provider_data_consent'])

    @override_settings(
        AI_ASSISTANT_API_KEY='',
        AI_ASSISTANT_MODEL='',
        AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER=True,
    )
    @patch('axis_saas.views.ai.assistant._rate_limited', return_value=False)
    def test_chat_confirmation_is_ignored_without_provider_credentials(self, _rate_limited):
        conversation_id = '8f853ba6-68a4-4c86-9974-3bb9259076a4'
        request = self._request(
            'How many students were absent this week?',
            conversation_id=conversation_id,
            confirm_school_data_sharing=True,
        )
        response = assistant_api(request, 'demo')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['kind'], 'local_only')
        self.assertNotIn('ai_assistant_consent:demo', request.session)

    @patch('axis_saas.views.ai.assistant._rate_limited', return_value=False)
    def test_ending_chat_revokes_its_consent_and_history(self, _rate_limited):
        conversation_id = '8f853ba6-68a4-4c86-9974-3bb9259076a4'
        request = self._request('', conversation_id=conversation_id, action='end_chat')
        request.session['ai_assistant_consent:demo'] = conversation_id
        request.session[f'ai_assistant_history:demo:{conversation_id}'] = [
            {'role': 'assistant', 'content': 'School data answer'},
        ]
        response = assistant_api(request, 'demo')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('ai_assistant_consent:demo', request.session)
        self.assertNotIn(f'ai_assistant_history:demo:{conversation_id}', request.session)

    @patch('axis_saas.views.ai.assistant.run_assistant_model_turn')
    @patch('axis_saas.views.ai.assistant.lookup_students_by_parent_name')
    @patch('axis_saas.views.ai.assistant._rate_limited', return_value=False)
    def test_parent_name_question_uses_local_student_lookup_without_provider(
        self, _rate_limited, lookup, provider,
    ):
        lookup.return_value = {'reply': 'Hazir Khan ke naam se 1 student record mila.', 'actions': []}
        response = assistant_api(
            self._request('Hazir Khan kis bache ka name he'),
            'demo',
        )
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertEqual(body['kind'], 'student_lookup')
        self.assertIn('1 student', body['reply'])
        lookup.assert_called_once_with('demo', 'hazir khan', roman_urdu=True)
        provider.assert_not_called()

    @patch('axis_saas.views.ai.assistant.run_assistant_model_turn')
    @patch('axis_saas.views.ai.assistant.class_pending_fee_summary')
    @patch('axis_saas.views.ai.assistant._rate_limited', return_value=False)
    def test_grade_section_pending_fee_question_uses_local_aggregate(
        self, _rate_limited, fee_summary, provider,
    ):
        fee_summary.return_value = {'reply': '10 section A ka current total pending fee 2500 hai.', 'actions': []}
        response = assistant_api(
            self._request('10 A ki total pending fee kitni hai'),
            'demo',
        )
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertEqual(body['kind'], 'fee_summary')
        fee_summary.assert_called_once_with('demo', '10', 'A', roman_urdu=True)
        provider.assert_not_called()

    @patch(
        'axis_saas.views.ai.assistant.run_assistant_model_turn',
        return_value={'reply': None, 'actions': [], 'tools_used': [], 'provider_status': 'unconfigured'},
    )
    @patch('axis_saas.views.ai.assistant._rate_limited', return_value=False)
    def test_inventory_how_to_uses_local_documentation_without_provider(
        self, _rate_limited, _provider,
    ):
        response = assistant_api(
            self._request('stock kese add kroo', path='/portal/demo/stock/'),
            'demo',
        )
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertEqual(body['kind'], 'documentation')
        self.assertIn('Add Product', body['reply'])
        self.assertIn('category', body['reply'].lower())

    @patch('axis_saas.views.ai.assistant.lookup_students')
    @patch('axis_saas.views.ai.assistant._rate_limited', return_value=False)
    def test_disabled_tenant_feature_blocks_student_lookup(self, _rate_limited, student_lookup):
        request = self._request('Sami name ke kitne students hain?')
        request.tenant.is_feature_enabled = lambda _feature, _channel: False
        response = assistant_api(request, 'demo')
        self.assertEqual(response.status_code, 404)
        self.assertIn('not enabled', json.loads(response.content)['error'])
        student_lookup.assert_not_called()

    @patch('axis_saas.views.ai.assistant.run_assistant_model_turn', return_value={'reply': 'Help answer', 'actions': [], 'tools_used': []})
    @patch('axis_saas.views.ai.assistant._rate_limited', return_value=False)
    def test_provider_context_uses_server_path_not_client_path(self, _rate_limited, provider):
        response = assistant_api(
            self._request(
                'How do I use this page?',
                current_path='/portal/demo/fee/collection/',
            ),
            'demo',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(provider.call_args.args[1], 'Fee collection')

    @patch('axis_saas.views.ai.assistant._rate_limited', return_value=False)
    @patch(
        'axis_saas.views.ai.assistant.run_assistant_model_turn',
        return_value={'reply': None, 'actions': [], 'tools_used': [], 'provider_status': 'unavailable'},
    )
    def test_provider_outage_is_not_reported_as_missing_configuration(self, _provider, _rate_limited):
        response = assistant_api(self._request('How does AXIS work?'), 'demo')
        self.assertEqual(response.status_code, 503)
        body = json.loads(response.content)
        self.assertTrue(body['provider_configured'])
        self.assertEqual(body['provider_status'], 'unavailable')

    @patch('axis_saas.views.ai.assistant._rate_limited', return_value=False)
    @patch(
        'axis_saas.views.ai.assistant.run_assistant_model_turn',
        return_value={'reply': None, 'actions': [], 'tools_used': [], 'provider_status': 'unconfigured'},
    )
    def test_missing_provider_configuration_is_exposed_in_response(self, _provider, _rate_limited):
        response = assistant_api(self._request('How does AXIS work?'), 'demo')
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertFalse(body['provider_configured'])
        self.assertEqual(body['provider_status'], 'unconfigured')

    @patch('axis_saas.views.ai.assistant.run_assistant_model_turn', return_value={'reply': 'Help answer', 'actions': [], 'tools_used': []})
    @patch('axis_saas.views.ai.assistant._rate_limited', return_value=False)
    def test_revoked_data_consent_purges_provider_history(self, _rate_limited, provider):
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
        definitions = enabled_tool_definitions(tenant, consent_confirmed=True)
        names = {item['function']['name'] for item in definitions}
        self.assertIn('search_students', names)
        self.assertIn('staff_attendance_range', names)
        self.assertNotIn('search_staff', names)
        self.assertNotIn('fee_collection_summary', names)
        self.assertNotIn('leave_request_summary', names)
        with self.assertRaises(ValueError):
            execute_tool(
                'delete_everything', '{}', tenant=tenant, schema_name='demo',
                consent_confirmed=True,
            )

    @override_settings(AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER=True)
    def test_school_data_tools_require_per_chat_confirmation(self):
        tenant = SimpleNamespace(
            is_feature_enabled=lambda feature, _channel: feature in {'students', 'ai_assistant'},
        )
        self.assertEqual(enabled_tool_definitions(tenant), [])
        names = {
            item['function']['name']
            for item in enabled_tool_definitions(tenant, consent_confirmed=True)
        }
        self.assertIn('query_school_data', names)
        self.assertNotIn('ai_assistant_data_sharing', names)

    @override_settings(AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER=True)
    def test_generic_query_schema_exposes_only_enabled_safe_datasets(self):
        tenant = SimpleNamespace(
            is_feature_enabled=lambda feature, _channel: feature in {
                'ai_assistant', 'ai_assistant_data_sharing', 'students',
            },
        )
        definitions = enabled_tool_definitions(tenant, consent_confirmed=True)
        query_tool = next(
            item['function'] for item in definitions
            if item['function']['name'] == 'query_school_data'
        )
        properties = query_tool['parameters']['properties']
        self.assertEqual(properties['dataset']['enum'], ['students'])
        allowed_fields = properties['fields']['items']['enum']
        self.assertIn('name', allowed_fields)
        self.assertIn('parent_mobile', allowed_fields)
        self.assertIn('father_cnic', allowed_fields)
        self.assertIn('notes', allowed_fields)

    @override_settings(AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER=True)
    @patch('axis_saas.views.ai.registry.query_school_data')
    def test_generic_query_execution_rechecks_dataset_feature(self, query):
        tenant = SimpleNamespace(
            is_feature_enabled=lambda feature, _channel: feature in {
                'ai_assistant', 'ai_assistant_data_sharing', 'students',
            },
        )
        query.return_value = {'dataset': 'students', 'operation': 'count', 'count': 12}
        result = execute_tool(
            'query_school_data',
            '{"dataset":"students","operation":"count"}',
            tenant=tenant,
            schema_name='demo',
            consent_confirmed=True,
        )
        self.assertEqual(result['count'], 12)
        query.assert_called_once_with(
            'demo', 'students', 'count', filters=None, metric='', group_by='',
            fields=None, limit=20, offset=0,
        )
        with self.assertRaises(PermissionError):
            execute_tool(
                'query_school_data',
                '{"dataset":"payments","operation":"count"}',
                tenant=tenant,
                schema_name='demo',
                consent_confirmed=True,
            )
        self.assertEqual(query.call_count, 1)

    @patch('axis_saas.views.ai.query.Student.objects.all')
    def test_generic_list_query_supports_offset_pages(self, student_queryset):
        queryset = MagicMock()
        student_queryset.return_value = queryset
        values_queryset = MagicMock()
        queryset.order_by.return_value.values.return_value = values_queryset
        values_queryset.__getitem__.return_value = [
            {'name': 'Student 3'},
            {'name': 'Student 4'},
            {'name': 'Student 5'},
        ]
        result = _execute_school_data_query(
            'students',
            'list',
            fields=['name'],
            limit=2,
            offset=2,
        )
        self.assertEqual(result['rows'], [{'name': 'Student 3'}, {'name': 'Student 4'}])
        self.assertTrue(result['truncated'])
        self.assertEqual(result['offset'], 2)
        self.assertEqual(result['next_offset'], 4)

    @patch('axis_saas.views.ai.query._execute_school_data_query')
    @patch('axis_saas.views.ai.query.schema_context')
    def test_generic_query_evaluation_runs_inside_requested_tenant_schema(
        self, tenant_context, execute_query,
    ):
        events = []
        context_manager = MagicMock()
        context_manager.__enter__.side_effect = lambda: events.append('entered')
        context_manager.__exit__.return_value = False
        tenant_context.return_value = context_manager
        execute_query.side_effect = lambda *_args, **_kwargs: {
            'inside_tenant_context': events == ['entered'],
        }
        result = query_school_data('school_alpha', 'students', 'count')
        tenant_context.assert_called_once_with('school_alpha')
        self.assertTrue(result['inside_tenant_context'])

    def test_query_dataset_fields_resolve_to_model_fields(self):
        for dataset_name, dataset in DATASETS.items():
            for alias, model_path in dataset['fields'].items():
                with self.subTest(dataset=dataset_name, field=alias):
                    self.assertIsNotNone(_resolve_model_field(dataset['model'], model_path))

    def test_public_tenant_and_authentication_models_are_never_queryable(self):
        model_names = {dataset['model'].__name__ for dataset in DATASETS.values()}
        self.assertTrue({
            'SchoolClient', 'SchoolDomain', 'StaffCredential',
            'StaffBiometricCredential',
        }.isdisjoint(model_names))

    def test_every_other_axis_model_has_a_tenant_query_dataset(self):
        app_models = set(apps.get_app_config('axis_saas').get_models())
        excluded_names = {
            'SchoolClient', 'SchoolDomain', 'StaffCredential',
            'StaffBiometricCredential',
        }
        expected_models = {
            model for model in app_models if model.__name__ not in excluded_names
        }
        self.assertEqual({dataset['model'] for dataset in DATASETS.values()}, expected_models)

    @patch('axis_saas.views.ai.query.Student.objects.all')
    def test_generic_query_excludes_binary_file_fields(self, student_queryset):
        with self.assertRaises(ValueError):
            _execute_school_data_query(
                'students',
                'list',
                filters=[{'field': 'photo', 'operator': 'eq', 'value': 'image.jpg'}],
                fields=['name'],
            )
        student_queryset.assert_called_once_with()

    def test_generic_query_requires_bounded_ranges_for_large_datasets(self):
        with self.assertRaises(ValueError):
            _validate_bounded_date_range(DATASETS['payments'], [])
        with self.assertRaises(ValueError):
            _validate_bounded_date_range(DATASETS['payments'], [
                {'field': 'date', 'operator': 'gte', 'value': '2025-01-01'},
                {'field': 'date', 'operator': 'lte', 'value': '2026-10-07'},
            ])
        _validate_bounded_date_range(DATASETS['payments'], [
            {'field': 'date', 'operator': 'gte', 'value': '2026-10-01'},
            {'field': 'date', 'operator': 'lte', 'value': '2026-10-07'},
        ])

    def test_aggregate_queries_can_cover_all_time_or_longer_periods(self):
        _validate_bounded_date_range(DATASETS['payments'], [], operation='sum')
        _validate_bounded_date_range(DATASETS['payments'], [
            {'field': 'date', 'operator': 'gte', 'value': '2020-01-01'},
            {'field': 'date', 'operator': 'lte', 'value': '2026-10-07'},
        ], operation='sum')

    def test_generic_query_null_filter_is_boolean_and_validated(self):
        field = _resolve_model_field(DATASETS['student_attendance']['model'], 'period_order')
        self.assertIs(_coerce_filter_value('true', field, 'isnull'), True)
        self.assertIs(_coerce_filter_value('false', field, 'isnull'), False)
        with self.assertRaises(ValueError):
            _coerce_filter_value('maybe', field, 'isnull')

    @override_settings(AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER=True)
    @patch('axis_saas.views.ai.registry.attendance_range_summary')
    def test_attendance_range_tool_validates_dates_and_bounds(self, attendance_summary):
        tenant = SimpleNamespace(
            is_feature_enabled=lambda feature, _channel: feature in {
                'attendance_management', 'ai_assistant_data_sharing',
            },
        )
        attendance_summary.return_value = {'reply': 'Attendance summary', 'actions': []}
        result = execute_tool(
            'attendance_range',
            '{"start_date":"2026-10-01","end_date":"2026-10-07"}',
            tenant=tenant,
            schema_name='demo',
            consent_confirmed=True,
        )
        self.assertEqual(result['reply'], 'Attendance summary')
        attendance_summary.assert_called_once()
        for arguments in (
            '{"start_date":"2026-10-07","end_date":"2026-10-01"}',
            '{"start_date":"2025-01-01","end_date":"2026-10-07"}',
            '{"start_date":"not-a-date","end_date":"2026-10-07"}',
        ):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                execute_tool(
                    'attendance_range',
                    arguments,
                    tenant=tenant,
                    schema_name='demo',
                    consent_confirmed=True,
                )

    @override_settings(AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER=True)
    @patch('axis_saas.views.ai.registry.count_students')
    def test_student_count_tool_accepts_bounded_class_and_status_filters(self, count):
        tenant = SimpleNamespace(
            is_feature_enabled=lambda feature, _channel: feature in {
                'students', 'ai_assistant_data_sharing',
            },
        )
        count.return_value = {'reply': 'Filtered count', 'actions': []}
        execute_tool(
            'count_students',
            '{"grade":"Grade 6","section":"A","status":"active"}',
            tenant=tenant,
            schema_name='demo',
            consent_confirmed=True,
        )
        count.assert_called_once_with(
            'demo', roman_urdu=False, grade='Grade 6', section='A', status='active',
        )
        with self.assertRaises(ValueError):
            execute_tool(
                'count_students',
                '{"status":"deleted"}',
                tenant=tenant,
                schema_name='demo',
                consent_confirmed=True,
            )

    @override_settings(AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER=True)
    @patch('axis_saas.views.ai.registry.leave_request_summary')
    @patch('axis_saas.views.ai.registry.staff_attendance_summary')
    @patch('axis_saas.views.ai.registry.fee_collection_summary')
    def test_domain_summaries_dispatch_with_validated_dates(
        self, fee_summary, staff_summary, leave_summary,
    ):
        tenant = SimpleNamespace(
            is_feature_enabled=lambda feature, _channel: feature in {
                'fee_collection', 'reports', 'leave_management',
                'ai_assistant_data_sharing',
            },
        )
        cases = (
            ('fee_collection_summary', fee_summary),
            ('staff_attendance_range', staff_summary),
            ('leave_request_summary', leave_summary),
        )
        for tool_name, summary in cases:
            summary.return_value = {'reply': 'Verified summary', 'actions': []}
            with self.subTest(tool=tool_name):
                result = execute_tool(
                    tool_name,
                    '{"start_date":"2026-10-01","end_date":"2026-10-07"}',
                    tenant=tenant,
                    schema_name='demo',
                    consent_confirmed=True,
                )
                self.assertEqual(result['reply'], 'Verified summary')
            self.assertEqual(summary.call_count, 1)
            start_date, end_date = summary.call_args.args[1:3]
            self.assertEqual(start_date.isoformat(), '2026-10-01')
            self.assertEqual(end_date.isoformat(), '2026-10-07')

    def test_widget_template_compiles(self):
        self.assertIsNotNone(get_template('tenant/ai/widget.html'))

    def test_shared_admin_header_always_mounts_assistant_launcher(self):
        base_template = Path(settings.BASE_DIR, 'templates', 'tenant', 'base.html').read_text()
        self.assertIn('id="axis-ai-header-trigger"', base_template)
        self.assertIn("{% include 'tenant/ai/widget.html' %}", base_template)
