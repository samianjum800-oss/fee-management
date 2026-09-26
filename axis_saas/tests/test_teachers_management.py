"""Tests for TEACHERS_MANAGEMENT_V1.

Covers URL resolution, module imports, template presence, view module
contract, and the legacy /classes/ redirect target.
"""
import ast
from pathlib import Path

from django.test import SimpleTestCase
from django.urls import resolve, reverse


class TeachersManagementURLTests(SimpleTestCase):
    def test_teachers_management_url(self):
        url = reverse('teachers_management', kwargs={'schema_name': 'ey'})
        self.assertEqual(url, '/portal/ey/teachers/')

    def test_teachers_management_subjects_url(self):
        url = reverse(
            'teachers_management_subjects', kwargs={'schema_name': 'ey'},
        )
        self.assertEqual(url, '/portal/ey/teachers/subjects/')

    def test_teachers_management_assignments_url(self):
        url = reverse(
            'teachers_management_assignments', kwargs={'schema_name': 'ey'},
        )
        self.assertEqual(url, '/portal/ey/teachers/assignments/')

    def test_teachers_management_class_teachers_url(self):
        url = reverse(
            'teachers_management_class_teachers',
            kwargs={'schema_name': 'ey'},
        )
        self.assertEqual(url, '/portal/ey/teachers/class-teachers/')

    def test_legacy_classes_url_still_resolves(self):
        url = reverse('class_management', kwargs={'schema_name': 'ey'})
        self.assertEqual(url, '/portal/ey/classes/')

    def test_legacy_classes_resolves_to_redirect_view(self):
        match = resolve('/portal/ey/classes/')
        self.assertEqual(match.url_name, 'class_management')

    def test_new_teachers_url_resolves_to_view(self):
        match = resolve('/portal/ey/teachers/')
        self.assertEqual(match.url_name, 'teachers_management')

    def test_new_subjects_url_sets_active_tab(self):
        match = resolve('/portal/ey/teachers/subjects/')
        self.assertEqual(match.url_name, 'teachers_management_subjects')
        self.assertEqual(match.kwargs.get('active_tab'), 'subjects')

    def test_new_assignments_url_sets_active_tab(self):
        match = resolve('/portal/ey/teachers/assignments/')
        self.assertEqual(match.kwargs.get('active_tab'), 'assignments')

    def test_new_class_teachers_url_sets_active_tab(self):
        match = resolve('/portal/ey/teachers/class-teachers/')
        self.assertEqual(match.kwargs.get('active_tab'), 'class-teachers')


class TeachersManagementTemplateTests(SimpleTestCase):
    def test_template_file_exists(self):
        project_root = Path(__file__).resolve().parents[2]
        tpl = project_root / 'templates' / 'tenant' / 'teachers_management.html'
        self.assertTrue(
            tpl.exists(),
            f'Missing template file: {tpl}',
        )

    def test_template_is_valid_html_skeleton(self):
        project_root = Path(__file__).resolve().parents[2]
        tpl = project_root / 'templates' / 'tenant' / 'teachers_management.html'
        if not tpl.exists():
            self.skipTest('Template not present')
        text = tpl.read_text(encoding='utf-8')
        self.assertIn("{% extends 'tenant/base.html' %}", text)
        self.assertIn('Teachers &amp; Academic Management', text)
        self.assertIn('teachers_management_subjects', text)
        self.assertIn('teachers_management_assignments', text)
        self.assertIn('teachers_management_class_teachers', text)

    def test_template_does_not_use_classes_sections_tab(self):
        project_root = Path(__file__).resolve().parents[2]
        tpl = project_root / 'templates' / 'tenant' / 'teachers_management.html'
        if not tpl.exists():
            self.skipTest('Template not present')
        text = tpl.read_text(encoding='utf-8').lower()
        self.assertNotIn('classes &amp; sections', text)
        self.assertNotIn('classes & sections', text)

    def test_template_uses_display_name_not_raw_str(self):
        """The template must rely on the pre-computed display_name so
        wing vs single school renders correctly."""
        project_root = Path(__file__).resolve().parents[2]
        tpl = project_root / 'templates' / 'tenant' / 'teachers_management.html'
        if not tpl.exists():
            self.skipTest('Template not present')
        text = tpl.read_text(encoding='utf-8')
        self.assertIn('cls.display_name', text)
        self.assertIn('a.class_display_name', text)


class TeachersManagementViewModuleTests(SimpleTestCase):
    def test_view_module_imports(self):
        from axis_saas.views.teachers_management import (
            VALID_TABS, teachers_management_redirect, teachers_management_view,
        )
        self.assertTrue(callable(teachers_management_view))
        self.assertTrue(callable(teachers_management_redirect))
        self.assertEqual(
            set(VALID_TABS),
            {'subjects', 'assignments', 'class-teachers'},
        )

    def test_view_module_is_valid_python(self):
        import axis_saas.views.teachers_management as mod
        src = Path(mod.__file__).read_text(encoding='utf-8')
        ast.parse(src)


class TeachersManagementRedirectContractTests(SimpleTestCase):
    def test_redirect_view_returns_302(self):
        from axis_saas.views.teachers_management import (
            teachers_management_redirect,
        )
        from django.http import HttpResponseRedirect
        # The view calls django.shortcuts.redirect which returns a
        # HttpResponseRedirect — assert on the type without needing a
        # real tenant.
        from django.test import RequestFactory
        rf = RequestFactory()
        req = rf.get('/portal/ey/classes/')
        result = teachers_management_redirect(req, 'ey')
        self.assertIsInstance(result, HttpResponseRedirect)
        self.assertEqual(result.url, '/portal/ey/teachers/')


class TeachersManagementFeatureGateTests(SimpleTestCase):
    def test_view_module_declares_required_decorators(self):
        """Sanity check: the view must still be feature-gated on
        `class_management`, matching the previous URL behaviour."""
        import axis_saas.views.teachers_management as mod
        src = Path(mod.__file__).read_text(encoding='utf-8')
        self.assertIn("@require_school_feature('class_management')", src)
        self.assertIn("@require_tenant_type(['school'])", src)
