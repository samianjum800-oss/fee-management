from decimal import Decimal

from django.test import Client, TestCase
from django_tenants.utils import schema_context

from axis_saas.models import (
    ClassTimetableAssignment,
    FeeStructure,
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
            enabled_features=["class_management", "classes_management", "fee_structure"],
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

    def test_fee_modal_uses_fee_structure_backend_and_shows_class_status(self):
        with schema_context(self.tenant.schema_name):
            school_class = SchoolClass.objects.create(name="5", section="A")

        response = self.client.post(
            f"/portal/{self.tenant.schema_name}/fee/structure/",
            {
                "class_id": str(school_class.pk),
                "monthly_fee": "1250.50",
                "return_to": "classes_management",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("open_fee_structure=1", response["Location"])

        with schema_context(self.tenant.schema_name):
            fee = FeeStructure.objects.get(grade="5 - A")
            self.assertEqual(fee.monthly_fee, Decimal("1250.50"))

        edit_response = self.client.post(
            f"/portal/{self.tenant.schema_name}/fee/structure/",
            {
                "class_id": str(school_class.pk),
                "monthly_fee": "1600.00",
                "return_to": "classes_management",
            },
        )
        self.assertEqual(edit_response.status_code, 302)
        self.assertNotIn("open_fee_structure=1", edit_response["Location"])
        with schema_context(self.tenant.schema_name):
            self.assertEqual(FeeStructure.objects.get(grade="5 - A").pk, fee.pk)
            self.assertEqual(
                FeeStructure.objects.get(grade="5 - A").monthly_fee,
                Decimal("1600.00"),
            )

        page_response = self.client.get(f"/portal/{self.tenant.schema_name}/my-classes/")
        self.assertEqual(page_response.status_code, 200)
        self.assertContains(page_response, "Fee set")
        self.assertContains(page_response, "View class")
        self.assertContains(page_response, "5 - A")

    def test_readding_wing_class_restores_the_class_in_its_original_wing(self):
        self.tenant.tenant_type = "wing_school"
        self.tenant.save(update_fields=["tenant_type"])
        with schema_context(self.tenant.schema_name):
            campus = WingCategory.objects.create(name="North")
            wing = WingCategory.objects.create(name="Original Wing", parent=campus)
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
        self.assertContains(classes_response, "Campus Management")
        self.assertContains(classes_response, "Campus management")
        self.assertContains(
            classes_response,
            f"/portal/{self.tenant.schema_name}/my-classes/{school_class.pk}/?show_timetable=1",
        )

        campus_response = self.client.post(
            f"/portal/{self.tenant.schema_name}/settings/",
            {
                "return_to": "classes_management",
                "category_action": "add",
                "main_category": "South",
                "sub_category": "Junior",
            },
        )
        self.assertEqual(campus_response.status_code, 302)
        self.assertIn("open_campus_management=1", campus_response["Location"])
        with schema_context(self.tenant.schema_name):
            self.assertTrue(
                WingCategory.objects.filter(
                    name="Junior",
                    parent__name="South",
                    is_active=True,
                ).exists()
            )

    def test_campus_management_edits_adds_and_deactivates_wings_and_campus(self):
        self.tenant.tenant_type = "wing_school"
        self.tenant.save(update_fields=["tenant_type"])
        with schema_context(self.tenant.schema_name):
            campus = WingCategory.objects.create(name="North")
            wing = WingCategory.objects.create(name="Junior", parent=campus)
            removed_wing = WingCategory.objects.create(name="Old Wing", parent=campus)

        edit_response = self.client.post(
            f"/portal/{self.tenant.schema_name}/settings/",
            {
                "return_to": "classes_management",
                "category_action": "manage",
                "main_category_id": str(campus.pk),
                "category_id": str(campus.pk),
                "main_category": "North Campus",
                "subcategory_ids": [str(wing.pk), str(removed_wing.pk), ""],
                "subcategory_names": ["Junior School", "Old Wing", "Senior School"],
                "deleted_subcategories": [str(removed_wing.pk)],
            },
        )
        self.assertEqual(edit_response.status_code, 302)
        with schema_context(self.tenant.schema_name):
            campus.refresh_from_db()
            wing.refresh_from_db()
            removed_wing.refresh_from_db()
            self.assertEqual(campus.name, "North Campus")
            self.assertEqual(wing.name, "Junior School")
            self.assertTrue(WingCategory.objects.get(name="Senior School").is_active)
            self.assertFalse(removed_wing.is_active)

        delete_response = self.client.post(
            f"/portal/{self.tenant.schema_name}/settings/",
            {
                "return_to": "classes_management",
                "category_action": "delete_main",
                "category_id": str(campus.pk),
            },
        )
        self.assertEqual(delete_response.status_code, 302)
        with schema_context(self.tenant.schema_name):
            campus.refresh_from_db()
            wing.refresh_from_db()
            self.assertFalse(campus.is_active)
            self.assertFalse(wing.is_active)

    def test_adding_wing_to_an_existing_campus_does_not_require_new_campus_name(self):
        self.tenant.tenant_type = "wing_school"
        self.tenant.save(update_fields=["tenant_type"])
        with schema_context(self.tenant.schema_name):
            campus = WingCategory.objects.create(name="North")

        response = self.client.post(
            f"/portal/{self.tenant.schema_name}/settings/",
            {
                "return_to": "classes_management",
                "category_action": "add",
                "main_category_id": str(campus.pk),
                "main_category": "",
                "sub_category": "Senior Wing",
            },
        )
        self.assertEqual(response.status_code, 302)
        with schema_context(self.tenant.schema_name):
            self.assertTrue(
                WingCategory.objects.filter(
                    name="Senior Wing",
                    parent=campus,
                    is_active=True,
                ).exists()
            )

    def test_fee_classes_are_sorted_unset_first_then_highest_fee(self):
        with schema_context(self.tenant.schema_name):
            high_class = SchoolClass.objects.create(name="Grade 12", section="A")
            low_class = SchoolClass.objects.create(name="Grade 11", section="A")
            missing_class = SchoolClass.objects.create(name="Grade 10", section="A")
            FeeStructure.objects.create(grade="Grade 12 - A", monthly_fee=Decimal("2000"))
            FeeStructure.objects.create(grade="Grade 11 - A", monthly_fee=Decimal("1000"))

        response = self.client.get(f"/portal/{self.tenant.schema_name}/my-classes/")
        self.assertEqual(response.status_code, 200)
        fee_class_ids = [
            item.id for item in response.context["fee_classes"]
        ]
        self.assertEqual(fee_class_ids, [missing_class.id, high_class.id, low_class.id])
