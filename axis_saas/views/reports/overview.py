"""
AXIS views – reports module.
"""

import re
from django.shortcuts import render, redirect, get_object_or_404
import csv
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.db.models import Sum, Q, Exists, OuterRef, Max, F, Count, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncMonth, TruncDay
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db import connection
from django_tenants.utils import schema_context
from decimal import Decimal
from datetime import date, timedelta, datetime
from collections import defaultdict
import json
import re
from functools import wraps
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from ...models import (
    SchoolClient, Student, FeeStructure, FeeRecord, PaymentTransaction,
    SchoolFeeSettings, Product, ProductCategory, SaleItem, Staff,
    StaffCredential, StaffAttendance, StudentAttendance, LeaveRequest,
    StudentLeave, AttendanceAuditLog, SchoolClass, Subject, TimetableEntry,
)
from ...forms import StudentForm, FeeCollectionForm, FeeSettingsForm, FeeStructureForm, FamilyPaymentForm
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from ...models import ManualGenerationLog

from ..helpers import *
from axis_saas.utils.class_display import get_class_display_for_student, get_class_display_name

@require_tenant_type(['school'])
@require_school_feature('defaulters')
def defaulters(request, schema_name, force_mobile=False):
    """Defaulters list with search, filters, pagination, and analytics KPIs."""
    tenant = get_tenant(request, schema_name)
    q = request.GET.get('q', '').strip()
    grade = request.GET.get('grade', '')
    section = request.GET.get('section', '')
    days = request.GET.get('days', '0')
    sort_by = request.GET.get('sort_by', 'overdue')
    page_number = request.GET.get('page', 1)
    try:
        days = int(days)
    except:
        days = 0
    if days < 0:
        days = 0

    with schema_context(schema_name):
        today = timezone.localdate()
        cutoff = today - timedelta(days=days) if days > 0 else None
        students_qs = Student.objects.all()
        if q:
            students_qs = students_qs.filter(Q(name__icontains=q) | Q(roll_number__icontains=q) | Q(father_name__icontains=q) | Q(father_cnic__icontains=q) | Q(parent_mobile__icontains=q))
        if grade:
            students_qs = students_qs.filter(grade=grade)
        if section:
            students_qs = students_qs.filter(section=section)

        students_qs = get_student_pending_queryset(students_qs)
        students_qs = students_qs.filter(pending_amount__gt=0)

        if cutoff:
            students_qs = students_qs.filter(fee_records__due_date__lt=cutoff)
        students_qs = students_qs.distinct()

        if sort_by == 'pending':
            students_qs = students_qs.order_by('-pending_amount', 'name')
        elif sort_by == 'name':
            students_qs = students_qs.order_by('name')
        else:
            students_qs = students_qs.order_by('-pending_amount', 'name')

        # Build defaulters_data list
        defaulters_data = []
        total_pending_all = Decimal('0')
        for student in students_qs:
            pending = student.pending_amount
            total_pending_all += pending
            # Compute days overdue
            oldest_due = student.fee_records.filter(status__in=['pending', 'partial', 'overdue']).order_by('due_date').first()
            days_overdue = (today - oldest_due.due_date).days if oldest_due and oldest_due.due_date < today else 0
            display_class = get_class_display_for_student(student, tenant)

            defaulters_data.append({
                'student': student,
                'pending_amount': pending,
                'fee_pending': pending,
                'days_overdue': days_overdue,
                'display_class': display_class,
            })

        total_defaulters = len(defaulters_data)

        # Paginate
        paginator = Paginator(defaulters_data, 15)
        page_obj = paginator.get_page(page_number)

        # Compute avg and max overdue from the full list
        avg_overdue = 0
        max_overdue = 0
        if total_defaulters > 0:
            total_days = sum(item['days_overdue'] for item in defaulters_data)
            avg_overdue = total_days / total_defaulters
            max_overdue = max(item['days_overdue'] for item in defaulters_data)

        grades = list(Student.objects.values_list('grade', flat=True).distinct().order_by('grade'))
        sections = list(Student.objects.values_list('section', flat=True).distinct().order_by('section'))

    context = {
        'tenant': tenant,
        'defaulters': page_obj,
        'total_defaulters': total_defaulters,
        'total_pending_all': total_pending_all,
        'avg_overdue': round(avg_overdue, 1),
        'max_overdue': max_overdue,
        'days': days,
        'search_query': q,
        'grade_filter': grade,
        'section_filter': section,
        'sort_by': sort_by,
        'grades': grades,
        'sections': sections,
        'logo_url': tenant.school_logo.url if tenant.school_logo else None,
    }
    template = 'mobile/defaulters.html' if force_mobile else 'tenant/defaulters.html'
    return render(request, template, context)

@require_tenant_type(['school'])
@require_school_feature('reports')
def reports(request, schema_name, force_mobile=False):
    tenant = get_tenant(request, schema_name)
    report_type = request.GET.get('type', 'collection')
    today = timezone.localdate()
    quick_filter = request.GET.get('quick_filter')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    search_q = request.GET.get('search', '').strip()
    page_num = request.GET.get('page', 1)
    if quick_filter == 'today':
        start_date = end_date = today
    elif quick_filter == 'yesterday':
        start_date = end_date = today - timedelta(days=1)
    elif quick_filter == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif quick_filter == 'last7days':
        start_date = today - timedelta(days=6)
        end_date = today
    elif quick_filter == 'last30days':
        start_date = today - timedelta(days=29)
        end_date = today
    elif quick_filter == 'month':
        start_date = today.replace(day=1)
        end_date = today
    elif quick_filter == 'quarter':
        quarter_month = ((today.month - 1) // 3) * 3 + 1
        start_date = today.replace(month=quarter_month, day=1)
        end_date = today
    elif quick_filter == 'year':
        start_date = today.replace(month=1, day=1)
        end_date = today
    elif quick_filter == 'all':
        start_date = date(2000, 1, 1)
        end_date = today
    elif quick_filter == 'last6months':
        start_date = today - timedelta(days=180)
        end_date = today
    elif start_date_str and end_date_str:
        try:
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
            if start_date > end_date:
                start_date, end_date = (end_date, start_date)
            quick_filter = 'custom'
        except:
            start_date = today - timedelta(days=180)
            end_date = today
            quick_filter = 'last6months'
    else:
        start_date = date(2000, 1, 1)
        end_date = today
        quick_filter = 'all'
    with schema_context(schema_name):
        payments_qs = PaymentTransaction.objects.filter(payment_date__gte=start_date, payment_date__lte=end_date)
        if search_q:
            payments_qs = payments_qs.filter(Q(receipt_number__icontains=search_q) | Q(student__name__icontains=search_q) | Q(student__roll_number__icontains=search_q))

        if request.GET.get('format') == 'csv':
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="collection-{start_date}-{end_date}.csv"'
            response.write('\ufeff')
            writer = csv.writer(response)
            writer.writerow(['Receipt', 'Student', 'Roll number', 'Grade', 'Section', 'Amount', 'Date', 'Payment mode', 'Collected by', 'Remarks'])
            for payment in payments_qs.select_related('student').order_by('-payment_date', '-id').iterator(chunk_size=500):
                cells = [
                    payment.receipt_number, payment.student.name,
                    payment.student.roll_number, payment.student.grade,
                    payment.student.section, payment.amount, payment.payment_date,
                    payment.get_payment_mode_display(), payment.created_by,
                    payment.remarks,
                ]
                writer.writerow([
                    "'" + str(value) if str(value or '').startswith(('=', '+', '-', '@', '\t', '\r')) else value
                    for value in cells
                ])
            return response

        paginator = Paginator(payments_qs.order_by('-payment_date'), 15)
        payments_page = paginator.get_page(page_num)
        total_collection = payments_qs.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        payment_count = payments_qs.count()
        total_pending = FeeRecord.objects.aggregate(total=Sum(F('amount') - F('paid_amount')))['total'] or Decimal('0')
        total_collection_all = PaymentTransaction.objects.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        total_billed = total_collection_all + total_pending
        collection_rate = float(total_collection_all) / float(total_billed) * 100 if total_billed > 0 else 0
        defaulters_count = Student.objects.filter(fee_records__status__in=['pending', 'partial', 'overdue']).distinct().count()
        monthly_data = []
        for i in range(5, -1, -1):
            m = today.month - i
            y = today.year
            if m <= 0:
                m += 12
                y -= 1
            total = PaymentTransaction.objects.filter(payment_date__year=y, payment_date__month=m).aggregate(Sum('amount'))['amount__sum'] or 0
            monthly_data.append({'month': f'{m}/{y}', 'amount': float(total)})
        mode_totals = {}
        for mode_code, mode_name in PaymentTransaction.PAYMENT_MODE_CHOICES:
            total = payments_qs.filter(payment_mode=mode_code).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
            if total > 0:
                mode_totals[mode_name] = float(total)
        mode_distribution = [{'name': k, 'amount': v} for k, v in mode_totals.items()]
        class_pending = []
        grades = Student.objects.values_list('grade', flat=True).distinct().order_by('grade')
        grades = list(grades)
        for grade in grades:
            pending = get_student_pending_queryset(Student.objects.filter(grade=grade)).aggregate(total_pending=Sum('pending_amount'))['total_pending'] or Decimal('0')
            if pending > 0:
                class_pending.append({'grade': grade, 'pending': float(pending)})
        class_pending.sort(key=lambda x: x['pending'], reverse=True)
        top_defaulters = []
        for student in get_student_pending_queryset(Student.objects.all()).filter(pending_amount__gt=0).order_by('-pending_amount')[:5]:
            top_defaulters.append({'student': student, 'pending': float(student.pending_amount)})
        defaulters_list = Student.objects.filter(fee_records__status__in=['pending', 'partial', 'overdue']).distinct()
        defaulters_data = []
        for student in get_student_pending_queryset(defaulters_list).prefetch_related('fee_records'):
            pending = student.pending_amount
            oldest_due = student.fee_records.filter(status__in=['pending', 'partial', 'overdue']).order_by('due_date').first()
            days_overdue = (timezone.localdate() - oldest_due.due_date).days if oldest_due and oldest_due.due_date < timezone.localdate() else 0
            defaulters_data.append({'student': student, 'pending_amount': pending, 'fee_pending': pending, 'days_overdue': days_overdue})

        student_status_counts = {
            row['status']: row['count']
            for row in Student.objects.values('status').annotate(count=Count('id'))
        }
        student_attendance = StudentAttendance.objects.filter(date__range=(start_date, end_date))
        student_attendance_totals = student_attendance.aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(status='present')),
            late=Count('id', filter=Q(status='late')),
            half_day=Count('id', filter=Q(status='half_day')),
            absent=Count('id', filter=Q(status='absent')),
            excused=Count('id', filter=Q(status='excused')),
        )
        student_attendance_denominator = sum(
            student_attendance_totals[key] for key in ('present', 'late', 'half_day', 'absent')
        )
        student_attendance_totals['rate'] = round(
            (student_attendance_totals['present'] + student_attendance_totals['late'] + student_attendance_totals['half_day'])
            / student_attendance_denominator * 100, 1
        ) if student_attendance_denominator else 0

        staff_attendance = StaffAttendance.objects.filter(date__range=(start_date, end_date))
        staff_attendance_totals = staff_attendance.aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(status='present')),
            late=Count('id', filter=Q(status='late')),
            half_day=Count('id', filter=Q(status='half_day')),
            absent=Count('id', filter=Q(status='absent')),
            on_leave=Count('id', filter=Q(status='on_leave')),
        )
        staff_attendance_denominator = sum(
            staff_attendance_totals[key] for key in ('present', 'late', 'half_day', 'absent')
        )
        staff_attendance_totals['rate'] = round(
            (staff_attendance_totals['present'] + staff_attendance_totals['late'] + staff_attendance_totals['half_day'])
            / staff_attendance_denominator * 100, 1
        ) if staff_attendance_denominator else 0
        most_absent_staff = list(
            staff_attendance.filter(status='absent')
            .values('staff_id', 'staff__full_name', 'staff__job_title')
            .annotate(absences=Count('id')).order_by('-absences')[:8]
        )

        leave_requests = LeaveRequest.objects.filter(created_at__date__range=(start_date, end_date))
        leave_status_counts = {
            row['status']: row['count']
            for row in leave_requests.values('status').annotate(count=Count('id'))
        }
        recent_leave_requests = leave_requests.select_related('staff').order_by('-created_at')[:8]
        student_leave_requests = StudentLeave.objects.filter(created_at__date__range=(start_date, end_date))
        student_leave_counts = {
            row['status']: row['count']
            for row in student_leave_requests.values('status').annotate(count=Count('id'))
        }
        recent_student_leaves = student_leave_requests.select_related('student').order_by('-created_at')[:8]
        most_absent_students = list(
            student_attendance.filter(status='absent')
            .values('student_id', 'student__name', 'student__grade', 'student__section')
            .annotate(absences=Count('id')).order_by('-absences')[:8]
        )

        products = Product.objects.select_related('category')
        inventory_totals = products.aggregate(
            products=Count('id'),
            units=Sum('quantity'),
            stock_value=Sum(ExpressionWrapper(
                F('quantity') * F('selling_price'),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )),
        )
        inventory_totals['units'] = inventory_totals['units'] or 0
        inventory_totals['stock_value'] = inventory_totals['stock_value'] or Decimal('0')
        low_stock_products = products.filter(quantity__lte=5).order_by('quantity', 'name')[:12]
        sales = SaleItem.objects.filter(payment__payment_date__range=(start_date, end_date))
        sales_totals = sales.aggregate(
            revenue=Sum('line_total'),
            units=Sum('quantity'),
            lines=Count('id'),
        )
        sales_totals['revenue'] = sales_totals['revenue'] or Decimal('0')
        sales_totals['units'] = sales_totals['units'] or 0
        sales_totals['lines'] = sales_totals['lines'] or 0
        top_selling_products = list(
            sales.values('name').annotate(units=Sum('quantity'), revenue=Sum('line_total'))
            .order_by('-revenue')[:5]
        )

        attendance_audits = AttendanceAuditLog.objects.filter(
            changed_at__date__range=(start_date, end_date)
        ).select_related('changed_by').order_by('-changed_at')[:12]
        generation_logs = ManualGenerationLog.objects.filter(
            generated_at__date__range=(start_date, end_date)
        )[:8]

        staff_members = list(Staff.objects.only(
            'id', 'staff_id', 'full_name', 'job_title', 'department', 'status',
        ).order_by('full_name'))
        staff_ids = [staff.pk for staff in staff_members]
        with schema_context('public'):
            credentials = {
                credential.staff_id: credential.last_login
                for credential in StaffCredential.objects.filter(
                    schema_name=schema_name, staff_id__in=staff_ids,
                ).only('staff_id', 'last_login')
            }
        online_cache_keys = {
            f'staff_online:{schema_name}:{staff.pk}': staff.pk
            for staff in staff_members
        }
        try:
            active_staff_sessions = cache.get_many(online_cache_keys)
        except Exception:
            active_staff_sessions = {}
        staff_activity = [
            {
                'staff': staff,
                'is_online': bool(active_staff_sessions.get(
                    f'staff_online:{schema_name}:{staff.pk}'
                )),
                'last_login': credentials.get(staff.pk),
            }
            for staff in staff_members
        ]
        staff_activity.sort(
            key=lambda item: (
                item['is_online'],
                item['last_login'].timestamp() if item['last_login'] else 0,
            ),
            reverse=True,
        )
        online_staff_count = sum(item['is_online'] for item in staff_activity)
        online_staff_activity = [item for item in staff_activity if item['is_online']]
        recent_offline_staff_activity = [item for item in staff_activity if not item['is_online']][:20]
        recent_staff_activity = online_staff_activity + recent_offline_staff_activity

        academic_totals = {
            'classes': SchoolClass.objects.count(),
            'subjects': Subject.objects.count(),
            'timetable_entries': TimetableEntry.objects.count(),
        }

    # ---- add display_class to each defaulter ----
    for item in defaulters_data:
        student = item['student']
        item['display_class'] = get_class_display_for_student(student, tenant)

    defaulters_data.sort(key=lambda x: x['days_overdue'], reverse=True)
    context = {
        'tenant': tenant,
        'report_type': report_type,
        'start_date': start_date,
        'end_date': end_date,
        'quick_filter': quick_filter,
        'search_query': search_q,
        'total_collection': total_collection,
        'total_pending': total_pending,
        'collection_rate': round(collection_rate, 1),
        'defaulters_count': defaulters_count,
        'monthly_data': monthly_data,
        'mode_distribution': mode_distribution,
        'class_pending': class_pending,
        'top_defaulters': top_defaulters,
        'defaulters_data': defaulters_data,
        'payments': payments_page,
        'total': total_collection,
        'payment_count': payment_count,
        'logo_url': tenant.school_logo.url if tenant.school_logo else None,
        'total_collection_all': total_collection_all,
        'student_status_counts': student_status_counts,
        'student_count': sum(student_status_counts.values()),
        'student_attendance': student_attendance_totals,
        'staff_attendance': staff_attendance_totals,
        'most_absent_staff': most_absent_staff,
        'leave_status_counts': leave_status_counts,
        'recent_leave_requests': recent_leave_requests,
        'student_leave_counts': student_leave_counts,
        'recent_student_leaves': recent_student_leaves,
        'most_absent_students': most_absent_students,
        'inventory': inventory_totals,
        'low_stock_products': low_stock_products,
        'sales': sales_totals,
        'top_selling_products': top_selling_products,
        'attendance_audits': attendance_audits,
        'generation_logs': generation_logs,
        'staff_activity': recent_staff_activity,
        'online_staff_count': online_staff_count,
        'staff_count': len(staff_members),
        'academic_totals': academic_totals,
    }
    template = 'tenant/reports/mobile.html' if force_mobile else 'tenant/reports/overview.html'
    return render(request, template, context)

@require_tenant_type(['school'])
@require_school_feature('defaulters')
def mobile_defaulters(request, schema_name):
    """Mobile version of defaulters page."""
    return defaulters(request, schema_name, force_mobile=True)

@require_tenant_type(['school'])
@require_school_feature('reports')
def mobile_reports(request, schema_name):
    """Mobile version of reports page."""
    return reports(request, schema_name, force_mobile=True)
