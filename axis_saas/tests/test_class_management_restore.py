from django.test import Client, TestCase
from django_tenants.utils import schema_context

from axis_saas.models import (
    ClassTimetableAssignment,
    PeriodTeacherAssignment,
    PeriodsTimetable,
    ScheduleLabel,
    SchoolClass,
    SchoolClient,
    Student,
    WingCategory,
)


class ClassManagementRestoreTests(TestCase):
    def setUp(self):
        from django.db import connection

        connection.set_schema_to_public()
        self.tenant = SchoolClient.objects.create(
            schema_name="class-restore-test",
            name="Class Restore Test School",
            admin_username="admin",
            admin_password="admin123",
            tenant_type="single_small_school",
            enabled_features=["class_management", "classes_management"],
        )
        connection.set_schema_to_public()

        self.client = Client()
        session = self.client.session
        session["school_admin_authenticated"] = True
        session["school_admin_schema"] = self.tenant.schema_name
        session["school_admin_username"] = "admin"
        session.save()

    def tearDown(self):
        from django.db import connection

        connection.set_schema_to_public()
        try:
            self.tenant.delete(force_drop=True)
        except TypeError:
            self.tenant.delete()
        connection.set_schema_to_public()

    def test_readding_class_restores_its_existing_linked_records(self):
        with schema_context(self.tenant.schema_name):
            school_class = SchoolClass.objects.create(
                name="5",
                section="A",
                description="Keep this class setup",
                is_active=True,
            )
            student = Student.objects.create(
                name="Existing Student",
                father_name="Parent",
                father_cnic="35202-1234567-1",
                parent_mobile="03001234567",
                grade="5",
                section="A",
                school_class=school_class,
            )
            label = ScheduleLabel.objects.create(name="Senior")
            timetable = PeriodsTimetable.objects.create(
                title="Class 5 timetable",
                label=label,
                days=[{"day_of_week": 0, "periods_count": 1}],
            )
            timetable_assignment = ClassTimetableAssignment.objects.create(
                school_class=school_class,
                timetable=timetable,
            )
            period_teacher_assignment = PeriodTeacherAssignment.objects.create(
                school_class=school_class,
                day_of_week=0,
                period_order=1,
            )

        delete_response = self.client.post(
            f"/portal/{self.tenant.schema_name}/classes/delete/{school_class.id}/",
            {"return_to": "classes_management"},
        )
        self.assertEqual(delete_response.status_code, 302)
        with schema_context(self.tenant.schema_name):
            school_class.refresh_from_db()
            self.assertFalse(school_class.is_active)

        add_response = self.client.post(
            f"/portal/{self.tenant.schema_name}/classes/add/",
            {
                "name": "5",
                "section": "A",
                "description": "",
                "return_to": "classes_management",
            },
        )
        self.assertEqual(add_response.status_code, 302)

        with schema_context(self.tenant.schema_name):
            school_class.refresh_from_db()
            self.assertTrue(school_class.is_active)
            self.assertEqual(school_class.description, "Keep this class setup")
            self.assertEqual(SchoolClass.objects.filter(name="5", section="A").count(), 1)
            self.assertEqual(Student.objects.get(pk=student.pk).school_class_id, school_class.pk)
            self.assertTrue(
                ClassTimetableAssignment.objects.filter(
                    pk=timetable_assignment.pk,
                    school_class=school_class,
                    timetable=timetable,
                ).exists()
            )
            self.assertTrue(
                PeriodTeacherAssignment.objects.filter(
                    pk=period_teacher_assignment.pk,
                    school_class=school_class,
                ).exists()
            )

    def test_class_card_links_to_its_timetable_modal(self):
        with schema_context(self.tenant.schema_name):
            school_class = SchoolClass.objects.create(name="5", section="A")

        response = self.client.get(f"/portal/{self.tenant.schema_name}/my-classes/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f"/portal/{self.tenant.schema_name}/my-classes/{school_class.pk}/?show_timetable=1",
        )

        detail_response = self.client.get(
            f"/portal/{self.tenant.schema_name}/my-classes/{school_class.pk}/?show_timetable=1"
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(
            detail_response,
            "new URLSearchParams(window.location.search).get('show_timetable') === '1'",
        )

    def test_readding_wing_class_restores_the_class_in_its_original_wing(self):
        self.tenant.tenant_type = "wing_school"
        self.tenant.save(update_fields=["tenant_type"])
        with schema_context(self.tenant.schema_name):
            wing = WingCategory.objects.create(name="North")
            school_class = SchoolClass.objects.create(
                name="5",
                section="A",
                wing_category=wing,
                is_active=False,
            )

        response = self.client.post(
            f"/portal/{self.tenant.schema_name}/classes/add/",
            {
                "name": "5",
                "section": "A",
                "wing_category": str(wing.pk),
                "return_to": "classes_management",
            },
        )
        self.assertEqual(response.status_code, 302)

        with schema_context(self.tenant.schema_name):
            school_class.refresh_from_db()
            self.assertTrue(school_class.is_active)
            self.assertEqual(school_class.wing_category_id, wing.pk)

        classes_response = self.client.get(
            f"/portal/{self.tenant.schema_name}/my-classes/"
        )
        self.assertEqual(classes_response.status_code, 200)
        self.assertContains(
            classes_response,
            f"/portal/{self.tenant.schema_name}/my-classes/{school_class.pk}/?show_timetable=1",
        )
