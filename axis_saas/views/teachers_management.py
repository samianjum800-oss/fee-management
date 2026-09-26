"""AXIS views — Teachers & Academic Management (TEACHERS_MANAGEMENT_V1).

Split out from the legacy `class_management` view. This view powers the
`/portal/<schema>/teachers/` page which now only handles:

    * Subjects catalog (CRUD)
    * Subject-to-class assignments
    * Class-teacher assignments

Each tab has its own URL:
    /portal/<schema>/teachers/                  -> Subjects (default)
    /portal/<schema>/teachers/subjects/         -> Subjects
    /portal/<schema>/teachers/assignments/      -> Assignments
    /portal/<schema>/teachers/class-teachers/   -> Class Teachers
"""
import logging

from django.shortcuts import redirect, render
from django.db.models import Count
from django_tenants.utils import schema_context

from ..forms import ClassSubjectForm, SubjectForm, available_wing_categories
from ..models import ClassSubject, SchoolClass, Staff, Student, Subject
from .helpers import (
    get_tenant, is_mobile_user_agent,
    require_school_feature, require_tenant_type,
)
from axis_saas.utils.class_display import get_class_display_name

logger = logging.getLogger(__name__)

VALID_TABS = ('subjects', 'assignments', 'class-teachers')


def _build_context(schema_name, tenant, active_tab):
    with schema_context(schema_name):
        classes = list(
            SchoolClass.objects
            .filter(is_active=True)
            .select_related(
                'class_teacher',
                'wing_category',
                'wing_category__parent',
            )
            .order_by('name', 'section')
        )
        for cls in classes:
            cls.display_name = get_class_display_name(cls, tenant.tenant_type)
            cls.student_count = Student.objects.filter(school_class=cls).count()

        subjects = list(
            Subject.objects.filter(is_active=True).order_by('name')
        )

        assignments = list(
            ClassSubject.objects
            .filter(is_active=True)
            .select_related(
                'school_class',
                'school_class__wing_category',
                'school_class__wing_category__parent',
                'subject',
                'teacher',
            )
            .order_by('school_class__name', 'subject__name')
        )
        for a in assignments:
            a.class_display_name = get_class_display_name(
                a.school_class, tenant.tenant_type,
            )

        teachers = list(
            Staff.objects.filter(status='active').order_by('full_name')
        )

        subject_form = SubjectForm()
        assign_form = ClassSubjectForm()
        assign_form.fields['teacher'].queryset = (
            Staff.objects.filter(status='active')
        )

        unassigned_subjects = (
            Subject.objects.filter(is_active=True)
            .exclude(
                id__in=ClassSubject.objects
                .filter(is_active=True)
                .values('subject_id')
            )
            .count()
        )

        classes_with_ct = sum(1 for c in classes if c.class_teacher_id)
        classes_without_ct = len(classes) - classes_with_ct
        subjects_with_teacher = sum(1 for a in assignments if a.teacher_id)

        top_subjects = list(
            ClassSubject.objects
            .filter(is_active=True)
            .values('subject__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        wing_categories = (
            available_wing_categories()
            if tenant.tenant_type == 'wing_school' else []
        )

    return {
        'tenant': tenant,
        'active_tab': active_tab,
        'classes': classes,
        'subjects': subjects,
        'assignments': assignments,
        'teachers': teachers,
        'subject_form': subject_form,
        'assign_form': assign_form,
        'wing_categories': wing_categories,
        'top_subjects': top_subjects,
        'analytics': {
            'total_classes': len(classes),
            'total_subjects': len(subjects),
            'total_assignments': len(assignments),
            'classes_with_ct': classes_with_ct,
            'classes_without_ct': classes_without_ct,
            'unassigned_subjects': unassigned_subjects,
            'subjects_with_teacher': subjects_with_teacher,
            'total_teachers': len(teachers),
        },
        'logo_url': tenant.school_logo.url if tenant.school_logo else None,
    }


@require_tenant_type(['school'])
@require_school_feature('class_management')
def teachers_management_view(request, schema_name, active_tab='subjects'):
    if is_mobile_user_agent(request):
        return redirect('mobile_class_management', schema_name=schema_name)
    if active_tab not in VALID_TABS:
        active_tab = 'subjects'
    tenant = get_tenant(request, schema_name)
    context = _build_context(schema_name, tenant, active_tab)
    response = render(request, 'tenant/teachers_management.html', context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def teachers_management_redirect(request, schema_name):
    """Legacy /classes/ URL -> /teachers/."""
    return redirect('teachers_management', schema_name=schema_name)
