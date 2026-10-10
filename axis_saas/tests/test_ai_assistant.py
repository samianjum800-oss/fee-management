import json
from types import SimpleNamespace
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase, override_settings
from django.template.loader import get_template

from axis_saas.admin import SchoolClientForm
from axis_saas.views.ai.intents import (
    extract_student_name_lookup,
    find_page_intent,
    is_roman_urdu,
    is_school_data_question,
    is_student_count_question,
)
from axis_saas.views.ai.knowledge import available_pages
from axis_saas.views.ai.providers import answer_general_question
from axis_saas.views.ai.assistant import assistant_api


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
        self.assertTrue(is_roman_urdu('Sami ke kitne students he?'))
        self.assertFalse(is_roman_urdu('How many students named Sami?'))

    def test_aggregate_count_does_not_misclassify_attendance_breakdown(self):
        self.assertTrue(is_student_count_question('Kitne students hain?'))
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


class AssistantConfigurationTests(SimpleTestCase):
    def test_admin_feature_is_desktop_opt_in(self):
        form = SchoolClientForm()
        self.assertIn(('ai_assistant', 'AI Assistant'), list(form.fields['desktop_features'].choices))
        self.assertNotIn('ai_assistant', form.fields['desktop_features'].initial)
        self.assertFalse(any(
            key == 'ai_assistant' for key, _label in form.fields['mobile_features'].choices
        ))

    @override_settings(AI_ASSISTANT_API_KEY='', AI_ASSISTANT_MODEL='')
    def test_general_provider_is_optional(self):
        self.assertIsNone(answer_general_question('How does AXIS work?', 'Dashboard', []))

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
        request.session = SimpleNamespace(session_key='assistant-test')
        return request

    @patch('axis_saas.views.ai.assistant.answer_general_question')
    def test_private_school_data_question_stays_local(self, provider):
        response = assistant_api(
            self._request('How many students were absent this week?'),
            'demo',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['kind'], 'local_only')
        provider.assert_not_called()

    @patch('axis_saas.views.ai.assistant.answer_general_question', return_value='Help answer')
    def test_provider_context_uses_server_path_not_client_path(self, provider):
        response = assistant_api(
            self._request(
                'How do I use this page?',
                current_path='/portal/demo/fee/collection/',
            ),
            'demo',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(provider.call_args.args[1], 'School reports')

    def test_widget_template_compiles(self):
        self.assertIsNotNone(get_template('tenant/ai/widget.html'))
