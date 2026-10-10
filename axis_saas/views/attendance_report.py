"""Read-only attendance reporting views and local insights."""

import csv
from datetime import date, timedelta

from django.core.paginator import Paginator
from django.db.models import CharField, Count, F, Q
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django_tenants.utils import schema_context

from ..models import (
    AttendanceAuditLog,
    SchoolClass,
    StaffAttendance,
    Student,
    StudentAttendance,
    WingCategory,
)
from .helpers import get_tenant, require_school_feature, require_tenant_type


ATTENDANCE_STATUSES = {value for value, _label in StudentAttendance.STATUS_CHOICES}
ATTENDANCE_SOURCES = {value for value, _label in StudentAttendance.SOURCE_CHOICES}


def _parse_date(value):
    try:
        return date.fromisoformat(value) if value else None
    except (TypeError, ValueError):
        return None


def _parse_id(value):
    try:
        parsed = int(value)
        return parsed if parsed > 0 else None
    except (TypeError, ValueError):
        return None


def _attendance_rate(row):
    eligible = row['present'] + row['late'] + row['half_day'] + row['absent']
    attended = row['present'] + row['late'] + row['half_day']
    return round(attended * 100 / eligible, 1) if eligible else 0


def _safe_csv_cell(value):
    value = '' if value is None else str(value)
    if value.startswith(('=', '+', '-', '@', '\t', '\r')):
        return "'" + value
    return value


@require_http_methods(['GET'])
@require_tenant_type(['school'])
@require_school_feature('reports')
@require_school_feature('attendance_management')
def attedence_report(request, schema_name):
    """Detailed, read-only attendance reports for a single tenant."""
    tenant = get_tenant(request, schema_name)
    today = timezone.localdate()
    quick_filter = request.GET.get('range', 'month')

    range_dates = {
        'today': (today, today),
        'yesterday': (today - timedelta(days=1), today - timedelta(days=1)),
        'week': (today - timedelta(days=today.weekday()), today),
        '7d': (today - timedelta(days=6), today),
        '30d': (today - timedelta(days=29), today),
        'month': (today.replace(day=1), today),
        'quarter': (today.replace(month=((today.month - 1) // 3) * 3 + 1, day=1), today),
        'year': (today.replace(month=1, day=1), today),
        'all': (date(2000, 1, 1), today),
    }
    start_date = _parse_date(request.GET.get('start_date'))
    end_date = _parse_date(request.GET.get('end_date'))
    if start_date and end_date:
        if start_date > end_date:
            start_date, end_date = end_date, start_date
        quick_filter = 'custom'
    else:
        start_date, end_date = range_dates.get(quick_filter, range_dates['month'])
        quick_filter = quick_filter if quick_filter in range_dates else 'month'

    campus_id = _parse_id(request.GET.get('campus'))
    wing_id = _parse_id(request.GET.get('wing'))
    class_id = _parse_id(request.GET.get('class_id'))
    section = request.GET.get('section', '').strip()[:20]
    status = request.GET.get('status', '').strip()
    status = status if status in ATTENDANCE_STATUSES else ''
    source = request.GET.get('source', '').strip()
    source = source if source in ATTENDANCE_SOURCES else ''
    period = request.GET.get('period', 'all').strip()
    search = request.GET.get('q', '').strip()[:100]

    with schema_context(schema_name):
        campuses = list(
            WingCategory.objects.filter(parent__isnull=True, is_active=True)
            .order_by('name')
        )
        campus = next((item for item in campuses if item.pk == campus_id), None)
        wings_qs = WingCategory.objects.filter(is_active=True)
        if campus:
            wings_qs = wings_qs.filter(parent_id=campus.pk)
        else:
            wings_qs = wings_qs.filter(parent__isnull=False)
        wings = list(wings_qs.order_by('name'))
        wing = next((item for item in wings if item.pk == wing_id), None)

        classes_qs = SchoolClass.objects.filter(is_active=True).select_related(
            'wing_category', 'wing_category__parent', 'class_teacher'
        ).annotate(
            active_students=Count('students', filter=Q(students__status='active'))
        ).order_by('wing_category__parent__name', 'wing_category__name', 'name', 'section')
        if campus:
            classes_qs = classes_qs.filter(
                Q(wing_category_id=campus.pk) | Q(wing_category__parent_id=campus.pk)
            )
        if wing:
            classes_qs = classes_qs.filter(wing_category_id=wing.pk)
        section_options = list(
            classes_qs.exclude(section='').values_list('section', flat=True)
            .distinct().order_by('section')
        )
        if section:
            classes_qs = classes_qs.filter(section__iexact=section)
        selected_class = classes_qs.filter(pk=class_id).first() if class_id else None
        if selected_class:
            classes_qs = classes_qs.filter(pk=selected_class.pk)

        scoped_records = StudentAttendance.objects.filter(
            date__range=(start_date, end_date)
        ).select_related(
            'student', 'school_class', 'school_class__wing_category',
            'school_class__wing_category__parent', 'marked_by', 'teacher',
        )
        if campus:
            scoped_records = scoped_records.filter(
                Q(school_class__wing_category_id=campus.pk)
                | Q(school_class__wing_category__parent_id=campus.pk)
            )
        if wing:
            scoped_records = scoped_records.filter(school_class__wing_category_id=wing.pk)
        if selected_class:
            scoped_records = scoped_records.filter(school_class_id=selected_class.pk)
        elif section:
            scoped_records = scoped_records.filter(school_class__section__iexact=section)
        if source:
            scoped_records = scoped_records.filter(source=source)
        if period == 'full_day':
            scoped_records = scoped_records.filter(period_order__isnull=True)
        elif period.isdigit() and int(period) > 0:
            scoped_records = scoped_records.filter(period_order=int(period))

        totals = scoped_records.aggregate(
            entries=Count('id'),
            students=Count('student_id', distinct=True),
            present=Count('id', filter=Q(status='present')),
            absent=Count('id', filter=Q(status='absent')),
            late=Count('id', filter=Q(status='late')),
            half_day=Count('id', filter=Q(status='half_day')),
            excused=Count('id', filter=Q(status='excused')),
            holiday=Count('id', filter=Q(status='holiday')),
        )
        totals['rate'] = _attendance_rate(totals)

        class_stats = {
            row['school_class_id']: row
            for row in scoped_records.values('school_class_id').annotate(
                entries=Count('id'),
                students=Count('student_id', distinct=True),
                present=Count('id', filter=Q(status='present')),
                absent=Count('id', filter=Q(status='absent')),
                late=Count('id', filter=Q(status='late')),
                half_day=Count('id', filter=Q(status='half_day')),
                excused=Count('id', filter=Q(status='excused')),
            )
        }
        class_rows = []
        for school_class in classes_qs:
            stats = class_stats.get(school_class.pk, {
                'entries': 0, 'students': 0, 'present': 0, 'absent': 0,
                'late': 0, 'half_day': 0, 'excused': 0,
            })
            stats = dict(stats)
            stats['rate'] = _attendance_rate(stats)
            stats['school_class'] = school_class
            class_rows.append(stats)

        campus_rows = list(
            scoped_records.values(campus_name=Coalesce(
                F('school_class__wing_category__parent__name'),
                F('school_class__wing_category__name'),
                output_field=CharField(),
            )).annotate(
                entries=Count('id'),
                students=Count('student_id', distinct=True),
                present=Count('id', filter=Q(status='present')),
                absent=Count('id', filter=Q(status='absent')),
                late=Count('id', filter=Q(status='late')),
                half_day=Count('id', filter=Q(status='half_day')),
                excused=Count('id', filter=Q(status='excused')),
            ).order_by('campus_name')
        )
        for row in campus_rows:
            row['rate'] = _attendance_rate(row)

        wing_rows = list(
            scoped_records.values(
                'school_class__wing_category_id',
                'school_class__wing_category__name',
                'school_class__wing_category__parent__name',
            ).annotate(
                entries=Count('id'),
                students=Count('student_id', distinct=True),
                present=Count('id', filter=Q(status='present')),
                absent=Count('id', filter=Q(status='absent')),
                late=Count('id', filter=Q(status='late')),
                half_day=Count('id', filter=Q(status='half_day')),
                excused=Count('id', filter=Q(status='excused')),
            ).order_by('school_class__wing_category__parent__name', 'school_class__wing_category__name')
        )
        for row in wing_rows:
            row['rate'] = _attendance_rate(row)

        student_attendance_filter = Q(attendance_records__date__range=(start_date, end_date))
        if campus:
            student_attendance_filter &= (
                Q(attendance_records__school_class__wing_category_id=campus.pk)
                | Q(attendance_records__school_class__wing_category__parent_id=campus.pk)
            )
        if wing:
            student_attendance_filter &= Q(attendance_records__school_class__wing_category_id=wing.pk)
        if selected_class:
            student_attendance_filter &= Q(attendance_records__school_class_id=selected_class.pk)
        elif section:
            student_attendance_filter &= Q(attendance_records__school_class__section__iexact=section)
        if source:
            student_attendance_filter &= Q(attendance_records__source=source)
        if period == 'full_day':
            student_attendance_filter &= Q(attendance_records__period_order__isnull=True)
        elif period.isdigit() and int(period) > 0:
            student_attendance_filter &= Q(attendance_records__period_order=int(period))

        students_qs = Student.objects.filter(status='active').select_related(
            'school_class', 'school_class__wing_category', 'school_class__wing_category__parent'
        )
        if campus or wing or selected_class:
            students_qs = students_qs.filter(school_class__in=classes_qs)
        elif section:
            students_qs = students_qs.filter(school_class__section__iexact=section)
        if search:
            students_qs = students_qs.filter(
                Q(name__icontains=search)
                | Q(roll_number__icontains=search)
                | Q(father_name__icontains=search)
            )
        students_qs = students_qs.annotate(
            entries=Count('attendance_records', filter=student_attendance_filter),
            present=Count('attendance_records', filter=student_attendance_filter & Q(attendance_records__status='present')),
            absent=Count('attendance_records', filter=student_attendance_filter & Q(attendance_records__status='absent')),
            late=Count('attendance_records', filter=student_attendance_filter & Q(attendance_records__status='late')),
            half_day=Count('attendance_records', filter=student_attendance_filter & Q(attendance_records__status='half_day')),
            excused=Count('attendance_records', filter=student_attendance_filter & Q(attendance_records__status='excused')),
        ).order_by('-absent', '-entries', 'name')
        student_paginator = Paginator(students_qs, 25)
        student_page = student_paginator.get_page(request.GET.get('student_page', 1))
        student_rows = list(student_page.object_list)
        for student in student_rows:
            student.rate = _attendance_rate({
                'present': student.present,
                'absent': student.absent,
                'late': student.late,
                'half_day': student.half_day,
            })

        detail_records = scoped_records
        if status:
            detail_records = detail_records.filter(status=status)
        if search:
            detail_records = detail_records.filter(
                Q(student__name__icontains=search)
                | Q(student__roll_number__icontains=search)
                | Q(student__father_name__icontains=search)
            )
        record_paginator = Paginator(detail_records.order_by('-date', 'student__roll_number', 'period_order'), 30)
        record_page = record_paginator.get_page(request.GET.get('record_page', 1))

        if request.GET.get('format') == 'csv':
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = (
                f'attachment; filename="attendance-{start_date}-{end_date}.csv"'
            )
            response.write('\ufeff')
            writer = csv.writer(response)
            writer.writerow([
                'Date', 'Campus', 'Wing', 'Class', 'Section', 'Student',
                'Roll number', 'Period', 'Status', 'Source', 'Marked by',
                'Marked at', 'Remarks',
            ])
            for record in detail_records.order_by('-date', 'student__roll_number').iterator(chunk_size=500):
                category = record.school_class.wing_category if record.school_class_id else None
                marker = record.marked_by or record.teacher
                writer.writerow([_safe_csv_cell(value) for value in (
                    record.date,
                    category.parent.name if category and category.parent_id else '',
                    category.name if category else '',
                    record.school_class.name if record.school_class_id else '',
                    record.school_class.section if record.school_class_id else '',
                    record.student.name if record.student_id else '',
                    record.student.roll_number if record.student_id else '',
                    record.period_order or 'Full day',
                    record.get_status_display(),
                    record.get_source_display(),
                    marker.full_name if marker else '',
                    record.marked_at,
                    record.remarks,
                )])
            return response

        daily_rows = list(
            scoped_records.filter(date__gte=max(start_date, end_date - timedelta(days=89)))
            .values('date')
            .annotate(
                present=Count('id', filter=Q(status='present')),
                absent=Count('id', filter=Q(status='absent')),
                late=Count('id', filter=Q(status='late')),
                half_day=Count('id', filter=Q(status='half_day')),
                excused=Count('id', filter=Q(status='excused')),
            ).order_by('date')
        )
        for row in daily_rows:
            row['date'] = row['date'].strftime('%d %b')

        source_rows = list(
            scoped_records.values('source').annotate(total=Count('id')).order_by('-total')
        )
        source_labels = dict(StudentAttendance.SOURCE_CHOICES)
        for row in source_rows:
            row['label'] = source_labels.get(row['source'], row['source'])

        audit_qs = AttendanceAuditLog.objects.filter(
            changed_at__date__range=(start_date, end_date)
        )
        if campus:
            audit_qs = audit_qs.filter(
                Q(attendance__school_class__wing_category_id=campus.pk)
                | Q(attendance__school_class__wing_category__parent_id=campus.pk)
            )
        if wing:
            audit_qs = audit_qs.filter(attendance__school_class__wing_category_id=wing.pk)
        if selected_class:
            audit_qs = audit_qs.filter(attendance__school_class_id=selected_class.pk)
        audit_rows = list(audit_qs.select_related(
            'attendance__student', 'attendance__school_class',
            'attendance__school_class__wing_category',
            'attendance__school_class__wing_category__parent', 'changed_by',
        ).order_by('-changed_at')[:12])

        full_day_marked_class_ids = set(
            StudentAttendance.objects.filter(
                date=end_date, period_order__isnull=True,
            ).values_list('school_class_id', flat=True).distinct()
        )
        if campus:
            compliance_classes = list(classes_qs)
        else:
            compliance_classes = list(classes_qs)
        unmarked_classes = [
            school_class for school_class in compliance_classes
            if school_class.pk not in full_day_marked_class_ids
        ] if start_date == end_date else []

        active_students = Student.objects.filter(status='active')
        if campus or wing or selected_class or section:
            active_students = active_students.filter(school_class__in=classes_qs)
        active_student_count = active_students.count()
        marked_active_student_count = scoped_records.filter(
            student__status='active'
        ).values('student_id').distinct().count()
        coverage_rate = round(
            min(100, marked_active_student_count * 100 / active_student_count), 1
        ) if active_student_count else 0

        staff_totals = StaffAttendance.objects.filter(date__range=(start_date, end_date)).aggregate(
            entries=Count('id'),
            present=Count('id', filter=Q(status='present')),
            absent=Count('id', filter=Q(status='absent')),
            late=Count('id', filter=Q(status='late')),
            on_leave=Count('id', filter=Q(status='on_leave')),
        )
        staff_totals['rate'] = round(
            (staff_totals['present'] + staff_totals['late']) * 100
            / (staff_totals['present'] + staff_totals['late'] + staff_totals['absent']), 1
        ) if staff_totals['present'] + staff_totals['late'] + staff_totals['absent'] else 0

        period_values = list(
            scoped_records.exclude(period_order__isnull=True)
            .values_list('period_order', flat=True).distinct().order_by('period_order')
        )

    top_absent_student = next((student for student in student_rows if student.absent), None)
    lowest_class = min(
        (row for row in class_rows if row['entries']),
        key=lambda row: row['rate'],
        default=None,
    )
    insights = {
        'rate': totals['rate'],
        'entries': totals['entries'],
        'absent': totals['absent'],
        'marked_students': totals['students'],
        'active_students': active_student_count,
        'coverage_rate': coverage_rate,
        'unmarked_classes': len(unmarked_classes) if start_date == end_date else None,
        'lowest_class': (
            f"{lowest_class['school_class']} ({lowest_class['rate']}%)"
            if lowest_class else None
        ),
        'top_absent_student': (
            f"{top_absent_student.name} ({top_absent_student.absent} absent marks)"
            if top_absent_student else None
        ),
    }
    context = {
        'tenant': tenant,
        'start_date': start_date,
        'end_date': end_date,
        'quick_filter': quick_filter,
        'campuses': campuses,
        'wings': wings,
        'classes': classes_qs,
        'section_options': section_options,
        'selected_campus': campus,
        'selected_wing': wing,
        'selected_class': selected_class,
        'selected_section': section,
        'selected_status': status,
        'selected_source': source,
        'selected_period': period,
        'search_query': search,
        'status_choices': StudentAttendance.STATUS_CHOICES,
        'source_choices': StudentAttendance.SOURCE_CHOICES,
        'period_values': period_values,
        'totals': totals,
        'active_student_count': active_student_count,
        'marked_active_student_count': marked_active_student_count,
        'coverage_rate': coverage_rate,
        'class_rows': class_rows,
        'campus_rows': campus_rows,
        'wing_rows': wing_rows,
        'student_page': student_page,
        'student_rows': student_rows,
        'record_page': record_page,
        'daily_rows': daily_rows,
        'source_rows': source_rows,
        'audit_rows': audit_rows,
        'unmarked_classes': unmarked_classes,
        'staff_totals': staff_totals,
        'insights': insights,
    }
    return render(request, 'tenant/reports/attedence.html', context)
