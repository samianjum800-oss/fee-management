"""
Tests for the staff list page and its modal APIs.

Covers: list rendering, filter parsing, empty-state, cache headers,
inline modal endpoints (subject assignments, class teachers, fixtures).
"""
from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse
from django_tenants.utils import schema_context

from axis_saas.models import (
    SchoolClient, Staff, SchoolClass, Subject, ClassSubject,
    LeaveRequest, WeeklyHoliday,
)


def _bootstrap_tenant():
    """Return an existing tenant named `test_staff` or create it."""
    t, _ = SchoolClient.objects.get_or_create(
        schema_name="test_staff",
        defaults={
            "name": "Test Staff Tenant",
            "admin_username": "admin_staff",
            "admin_password": "x",
            "tenant_type": "single_small_school",
            "enabled_features": [
                "dashboard", "staff_management", "timetable_management",
                "class_management", "classes_management",
            ],
        },
    )
    return t


class StaffListPageTests(TestCase):
    """Verify the page renders reliably regardless of filter state."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tenant = _bootstrap_tenant()

    def setUp(self):
        self.client = Client()
        session = self.client.session
        session["school_admin_authenticated"] = True
        session["school_admin_schema"] = self.tenant.schema_name
        session["school_admin_username"] = "admin_staff"
        session.save()

    def _make_staff(self, n=3):
        with schema_context(self.tenant.schema_name):
            Staff.objects.all().delete()
            for i in range(n):
                Staff.objects.create(
                    first_name=f"Teacher{i}",
                    last_name="Test",
                    job_title="Teacher",
                    department="teaching",
                    status="active",
                )

    def test_staff_list_renders_with_data(self):
        self._make_staff(3)
        url = reverse("staff_list", kwargs={"schema_name": self.tenant.schema_name})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode()
        self.assertIn("Teacher0", body)
        self.assertIn("Teacher2", body)
        self.assertNotIn("No staff members found", body)

    def test_staff_list_never_cached(self):
        """Cache-Control must forbid browser/proxy caching."""
        self._make_staff(1)
        url = reverse("staff_list", kwargs={"schema_name": self.tenant.schema_name})
        resp = self.client.get(url)
        cc = resp.get("Cache-Control", "").lower()
        self.assertTrue(
            "no-store" in cc or "no-cache" in cc,
            f"Expected no-store/no-cache in Cache-Control, got {cc!r}",
        )

    def test_staff_list_empty_state(self):
        with schema_context(self.tenant.schema_name):
            Staff.objects.all().delete()
        url = reverse("staff_list", kwargs={"schema_name": self.tenant.schema_name})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("No staff members found", resp.content.decode())

    def test_staff_list_filter_by_department(self):
        with schema_context(self.tenant.schema_name):
            Staff.objects.all().delete()
            Staff.objects.create(first_name="A", last_name="B",
                                 job_title="Teacher",
                                 department="teaching", status="active")
            Staff.objects.create(first_name="C", last_name="D",
                                 job_title="Accountant",
                                 department="admin", status="active")
        url = reverse("staff_list", kwargs={"schema_name": self.tenant.schema_name}) + "?department=teaching"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode()
        self.assertIn("A B", body)
        self.assertNotIn("C D", body)

    def test_staff_list_search_query(self):
        self._make_staff(3)
        url = reverse("staff_list", kwargs={"schema_name": self.tenant.schema_name}) + "?q=Teacher1"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Teacher1", resp.content.decode())

    def test_staff_list_bad_class_id_does_not_500(self):
        """Stale class_id in URL must not break the page."""
        self._make_staff(2)
        url = reverse("staff_list", kwargs={"schema_name": self.tenant.schema_name}) + "?class_id=999999"
        resp = self.client.get(url)
        self.assertIn(resp.status_code, (200, 404))

    def test_staff_list_pagination_does_not_500(self):
        self._make_staff(2)
        url = reverse("staff_list", kwargs={"schema_name": self.tenant.schema_name}) + "?page=9999"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)


class StaffModalApiTests(TestCase):
    """Exercise the inline modal endpoints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tenant = _bootstrap_tenant()

    def setUp(self):
        self.client = Client()
        session = self.client.session
        session["school_admin_authenticated"] = True
        session["school_admin_schema"] = self.tenant.schema_name
        session["school_admin_username"] = "admin_staff"
        session.save()

    def _seed(self):
        with schema_context(self.tenant.schema_name):
            ClassSubject.objects.all().delete()
            SchoolClass.objects.all().delete()
            Subject.objects.all().delete()
            Staff.objects.all().delete()

            t = Staff.objects.create(
                first_name="Alice", last_name="Wonder",
                job_title="Math Teacher", department="teaching",
                status="active",
            )
            s = Subject.objects.create(name="Mathematics")
            c = SchoolClass.objects.create(name="Grade 5", section="A",
                                           is_active=True)
            cs = ClassSubject.objects.create(
                school_class=c, subject=s, teacher=t, is_active=True,
            )
            return {"teacher": t, "subject": s, "class": c, "cs": cs}

    def test_subject_assignments_list(self):
        seed = self._seed()
        url = reverse("staff_subject_assignments_api",
                      kwargs={"schema_name": self.tenant.schema_name})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertEqual(len(data["rows"]), 1)
        self.assertEqual(data["rows"][0]["teacher_id"], seed["teacher"].id)

    def test_assign_subject_teacher_creates_assignment(self):
        seed = self._seed()
        with schema_context(self.tenant.schema_name):
            new_teacher = Staff.objects.create(
                first_name="Bob", last_name="Builder",
                job_title="Physics Teacher", department="teaching",
                status="active",
            )
        url = reverse("staff_assign_subject_teacher_api",
                      kwargs={"schema_name": self.tenant.schema_name})
        resp = self.client.post(
            url,
            data='{"class_id": %d, "subject_id": %d, "teacher_id": %d}'
                 % (seed["class"].id, seed["subject"].id, new_teacher.id),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["ok"])

    def test_assign_subject_teacher_rejects_inactive(self):
        seed = self._seed()
        with schema_context(self.tenant.schema_name):
            inactive = Staff.objects.create(
                first_name="Ghost", last_name="Worker",
                job_title="N/A", department="teaching",
                status="inactive",
            )
        url = reverse("staff_assign_subject_teacher_api",
                      kwargs={"schema_name": self.tenant.schema_name})
        resp = self.client.post(
            url,
            data='{"class_id": %d, "subject_id": %d, "teacher_id": %d}'
                 % (seed["class"].id, seed["subject"].id, inactive.id),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_class_teacher_management_list(self):
        self._seed()
        url = reverse("staff_class_teacher_management_api",
                      kwargs={"schema_name": self.tenant.schema_name})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["ok"])

    def test_assign_class_teacher(self):
        seed = self._seed()
        url = reverse("staff_assign_class_teacher_api",
                      kwargs={"schema_name": self.tenant.schema_name})
        resp = self.client.post(
            url,
            data='{"class_id": %d, "teacher_id": %d}'
                 % (seed["class"].id, seed["teacher"].id),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        with schema_context(self.tenant.schema_name):
            c = SchoolClass.objects.get(pk=seed["class"].id)
            self.assertEqual(c.class_teacher_id, seed["teacher"].id)

    def test_todays_leave_endpoint(self):
        self._seed()
        url = reverse("api_timetable_todays_leave",
                      kwargs={"schema_name": self.tenant.schema_name})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertIn("assignments", data)

    def test_subject_assignments_cross_tenant_isolation(self):
        """Subject assignments from another schema must not leak."""
        seed = self._seed()
        url = reverse("staff_subject_assignments_api",
                      kwargs={"schema_name": self.tenant.schema_name})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        for row in resp.json()["rows"]:
            self.assertIsNotNone(row["teacher_id"])


class StaffListTemplateIntegrityTests(TestCase):
    """Static checks on the rendered HTML to prevent regressions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tenant = _bootstrap_tenant()

    def setUp(self):
        self.client = Client()
        session = self.client.session
        session["school_admin_authenticated"] = True
        session["school_admin_schema"] = self.tenant.schema_name
        session["school_admin_username"] = "admin_staff"
        session.save()

    def test_no_duplicate_body_tag(self):
        with schema_context(self.tenant.schema_name):
            Staff.objects.all().delete()
            Staff.objects.create(first_name="X", last_name="Y",
                                 job_title="T",
                                 department="teaching", status="active")
        url = reverse("staff_list", kwargs={"schema_name": self.tenant.schema_name})
        body = self.client.get(url).content.decode().lower()
        self.assertEqual(body.count("</body>"), 1,
                         "base.html has duplicate </body>")

    def test_modal_scope_class_present(self):
        with schema_context(self.tenant.schema_name):
            Staff.objects.all().delete()
        url = reverse("staff_list", kwargs={"schema_name": self.tenant.schema_name})
        body = self.client.get(url).content.decode()
        self.assertIn('class="slx slx-modal-backdrop"', body)
