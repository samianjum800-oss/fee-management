"""Validated, read-only query surface for assistant access to school records."""

from datetime import date
from decimal import Decimal, InvalidOperation

from django.db.models import Avg, Count, F, Sum
from django_tenants.utils import schema_context

from ...models import (
    AcademicCalendar,
    AnnualHoliday,
    AttendanceAuditLog,
    AttendancePolicy,
    ClassSubject,
    ClassTeacherAttendancePermission,
    ClassTeacherEditQuota,
    ClassTimetableAssignment,
    DaySchedule,
    FeeRecord,
    FeeStructure,
    Holiday,
    LeavePolicy,
    LeaveRequest,
    LeaveSuspension,
    ManualGenerationLog,
    Notification,
    PaymentTransaction,
    Period,
    PeriodTeacherAssignment,
    PeriodsTimetable,
    Product,
    ProductCategory,
    SchoolFeeSettings,
    SaleItem,
    ScheduleLabel,
    SchoolClass,
    Staff,
    StaffAttendance,
    SubstituteAssignment,
    Student,
    StudentAttendance,
    StudentLeave,
    Subject,
    TimetableEntry,
    Vacation,
    WeeklyHoliday,
    WingCategory,
)


DATASETS = {
    'students': {
        'model': Student,
        'features': ('students',),
        'fields': {
            'name': 'name', 'roll_number': 'roll_number', 'grade': 'grade',
            'section': 'section', 'status': 'status', 'gender': 'gender',
            'admission_date': 'admission_date',
        },
        'metrics': (),
    },
    'staff': {
        'model': Staff,
        'features': ('staff_management',),
        'fields': {
            'name': 'full_name', 'staff_id': 'staff_id', 'job_title': 'job_title',
            'department': 'department', 'role': 'role', 'status': 'status',
            'hire_date': 'hire_date',
        },
        'metrics': (),
    },
    'fee_records': {
        'model': FeeRecord,
        'features': ('fee_collection',),
        'bounded_range_field': 'due_date',
        'guidance': 'base_amount excludes extra charges and late_fee; do not report base_amount as the final amount due.',
        'fields': {
            'student_name': 'student__name', 'roll_number': 'student__roll_number',
            'grade': 'student__grade', 'section': 'student__section',
            'month': 'month', 'year': 'year', 'base_amount': 'amount',
            'paid_amount': 'paid_amount', 'late_fee': 'late_fee_accrued',
            'due_date': 'due_date', 'status': 'status',
        },
        'metrics': ('base_amount', 'paid_amount', 'late_fee'),
    },
    'payments': {
        'model': PaymentTransaction,
        'features': ('fee_collection',),
        'bounded_range_field': 'date',
        'guidance': 'amount is recorded transaction collection during the selected date range; it is not the current outstanding balance.',
        'fields': {
            'student_name': 'student__name', 'grade': 'student__grade',
            'section': 'student__section', 'date': 'payment_date',
            'amount': 'amount', 'payment_mode': 'payment_mode',
            'payment_type': 'payment_type',
        },
        'metrics': ('amount',),
    },
    'student_attendance': {
        'model': StudentAttendance,
        'features': ('attendance_management',),
        'bounded_range_field': 'date',
        'guidance': 'Rows are marks, not unique students. period_order is NULL for full-day marks; use an isnull=true filter for full-day-only counts.',
        'fields': {
            'student_name': 'student__name', 'grade': 'student__grade',
            'section': 'student__section', 'class_name': 'school_class__name',
            'date': 'date', 'status': 'status', 'period_order': 'period_order',
            'source': 'source',
        },
        'metrics': (),
    },
    'staff_attendance': {
        'model': StaffAttendance,
        'features': ('reports',),
        'bounded_range_field': 'date',
        'guidance': 'Rows are daily staff attendance records; holiday and weekend statuses are separate from present/absent working-day counts.',
        'fields': {
            'staff_name': 'staff__full_name', 'date': 'date', 'status': 'status',
            'late_minutes': 'late_minutes', 'worked_minutes': 'worked_minutes',
            'source': 'source',
        },
        'metrics': ('late_minutes', 'worked_minutes'),
    },
    'staff_leave_requests': {
        'model': LeaveRequest,
        'features': ('leave_management',),
        'bounded_range_field': 'start_date',
        'guidance': 'Date bounds apply to leave start_date, not request submission date; use the dedicated leave summary for submission-date reporting.',
        'fields': {
            'staff_name': 'staff__full_name', 'leave_type': 'leave_type',
            'start_date': 'start_date', 'end_date': 'end_date',
            'days': 'total_days', 'status': 'status',
        },
        'metrics': ('days',),
    },
    'student_leave_requests': {
        'model': StudentLeave,
        'features': ('students', 'leave_management'),
        'bounded_range_field': 'start_date',
        'guidance': 'Date bounds apply to leave start_date. Reasons and reviewer notes are intentionally not exposed.',
        'fields': {
            'student_name': 'student__name', 'grade': 'student__grade',
            'section': 'student__section', 'leave_type': 'leave_type',
            'start_date': 'start_date', 'end_date': 'end_date',
            'days': 'total_days', 'status': 'status',
        },
        'metrics': ('days',),
    },
    'products': {
        'model': Product,
        'features': ('stock_management',),
        'fields': {
            'name': 'name', 'sku': 'sku', 'category': 'category__name',
            'quantity': 'quantity', 'selling_price': 'selling_price',
        },
        'metrics': ('quantity', 'selling_price'),
    },
    'sales': {
        'model': SaleItem,
        'features': ('stock_management', 'reports'),
        'bounded_range_field': 'date',
        'guidance': 'revenue is the recorded sale line total, filtered by the linked payment date.',
        'fields': {
            'product': 'name', 'student_name': 'payment__student__name',
            'date': 'payment__payment_date', 'quantity': 'quantity',
            'unit_price': 'unit_price', 'revenue': 'line_total',
        },
        'metrics': ('quantity', 'unit_price', 'revenue'),
    },
    'classes': {
        'model': SchoolClass,
        'features': ('classes_management',),
        'fields': {
            'name': 'name', 'section': 'section', 'is_active': 'is_active',
            'wing': 'wing_category__name',
        },
        'metrics': (),
    },
    'wing_categories': {
        'model': WingCategory,
        'features': ('classes_management',),
        'fields': {'name': 'name', 'parent': 'parent__name', 'is_active': 'is_active'},
        'metrics': (),
    },
    'subjects': {
        'model': Subject,
        'features': ('class_management',),
        'fields': {'name': 'name', 'code': 'code', 'is_active': 'is_active'},
        'metrics': (),
    },
    'class_subject_assignments': {
        'model': ClassSubject,
        'features': ('class_management',),
        'fields': {
            'class_name': 'school_class__name', 'section': 'school_class__section',
            'subject': 'subject__name', 'teacher': 'teacher__full_name',
            'academic_year': 'academic_year', 'is_active': 'is_active',
        },
        'metrics': (),
    },
    'timetable_entries': {
        'model': TimetableEntry,
        'features': ('timetable_management',),
        'guidance': 'day_of_week is an integer: Monday=0 through Sunday=6.',
        'fields': {
            'class_name': 'school_class__name', 'section': 'school_class__section',
            'day_of_week': 'day_of_week', 'period': 'period__order',
            'period_name': 'period__name', 'subject': 'subject__name',
            'teacher': 'teacher__full_name', 'academic_year': 'academic_year',
        },
        'metrics': (),
    },
    'period_teacher_assignments': {
        'model': PeriodTeacherAssignment,
        'features': ('timetable_management',),
        'fields': {
            'class_name': 'school_class__name', 'section': 'school_class__section',
            'day_of_week': 'day_of_week', 'period': 'period_order',
            'subject': 'subject__name', 'teacher': 'teacher__full_name',
        },
        'metrics': (),
    },
    'academic_calendar': {
        'model': AcademicCalendar,
        'features': ('timetable_management',),
        'fields': {
            'working_days': 'working_days', 'school_start_time': 'school_start_time',
            'school_end_time': 'school_end_time', 'period_duration': 'period_duration',
        },
        'metrics': ('period_duration',),
    },
    'periods': {
        'model': Period,
        'features': ('timetable_management',),
        'fields': {
            'name': 'name', 'order': 'order', 'start_time': 'start_time',
            'end_time': 'end_time', 'school_start_time': 'academic_calendar__school_start_time',
        },
        'metrics': ('order',),
    },
    'day_schedules': {
        'model': DaySchedule,
        'features': ('timetable_management',),
        'fields': {
            'day_of_week': 'day_of_week', 'label': 'label__name', 'order': 'order',
            'start_time': 'start_time', 'end_time': 'end_time', 'periods': 'periods',
            'duration': 'duration', 'is_active': 'is_active',
            'break_after': 'break_after', 'break_duration': 'break_duration',
        },
        'metrics': ('periods', 'duration', 'break_duration'),
    },
    'schedule_labels': {
        'model': ScheduleLabel,
        'features': ('timetable_management',),
        'fields': {'name': 'name', 'description': 'description'},
        'metrics': (),
    },
    'timetable_templates': {
        'model': PeriodsTimetable,
        'features': ('timetable_management',),
        'fields': {
            'title': 'title', 'label': 'label__name', 'break_duration': 'break_duration',
        },
        'metrics': ('break_duration',),
    },
    'class_timetable_assignments': {
        'model': ClassTimetableAssignment,
        'features': ('timetable_management', 'classes_management'),
        'fields': {
            'class_name': 'school_class__name', 'section': 'school_class__section',
            'timetable': 'timetable__title', 'label': 'timetable__label__name',
            'assigned_at': 'assigned_at',
        },
        'metrics': (),
    },
    'substitute_assignments': {
        'model': SubstituteAssignment,
        'features': ('timetable_management',),
        'bounded_range_field': 'date',
        'fields': {
            'absent_teacher': 'absent_teacher__full_name',
            'substitute_teacher': 'substitute_teacher__full_name',
            'class_name': 'school_class__name', 'section': 'school_class__section',
            'subject': 'subject__name', 'date': 'date',
            'day_of_week': 'day_of_week', 'period': 'period_order',
        },
        'metrics': (),
    },
    'holidays': {
        'model': Holiday,
        'features': ('timetable_management',),
        'bounded_range_field': 'date',
        'fields': {'date': 'date', 'name': 'name', 'recurring': 'is_recurring'},
        'metrics': (),
    },
    'weekly_holidays': {
        'model': WeeklyHoliday,
        'features': ('timetable_management',),
        'fields': {'day_of_week': 'day_of_week', 'label': 'label'},
        'metrics': (),
    },
    'annual_holidays': {
        'model': AnnualHoliday,
        'features': ('timetable_management',),
        'fields': {'month': 'month', 'day': 'day', 'label': 'label'},
        'metrics': (),
    },
    'vacations': {
        'model': Vacation,
        'features': ('timetable_management',),
        'bounded_range_field': 'start_date',
        'fields': {'name': 'name', 'start_date': 'start_date', 'end_date': 'end_date'},
        'metrics': (),
    },
    'attendance_audit': {
        'model': AttendanceAuditLog,
        'features': ('attendance_management',),
        'bounded_range_field': 'date',
        'fields': {
            'student_id': 'student_id_snapshot', 'date': 'date_snapshot',
            'period': 'period_snapshot', 'action': 'action',
            'old_status': 'old_status', 'new_status': 'new_status',
            'changed_by': 'changed_by_name', 'changed_at': 'changed_at',
        },
        'metrics': (),
    },
    'attendance_policy': {
        'model': AttendancePolicy,
        'features': ('attendance_management',),
        'fields': {
            'mode': 'attendance_mode', 'late_threshold_minutes': 'late_threshold_minutes',
            'low_attendance_threshold': 'low_attendance_threshold',
            'auto_mark_absent_at': 'auto_mark_absent_at',
            'notify_parents_on_absent': 'notify_parents_on_absent',
            'notify_after_periods': 'notify_after_periods',
            'allow_teacher_backdate_days': 'allow_teacher_backdate_days',
            'require_admin_approval': 'require_admin_approval',
        },
        'metrics': ('late_threshold_minutes', 'low_attendance_threshold', 'notify_after_periods'),
    },
    'class_attendance_permissions': {
        'model': ClassTeacherAttendancePermission,
        'features': ('attendance_management',),
        'fields': {
            'class_name': 'school_class__name', 'section': 'school_class__section',
            'backdate_access': 'backdate_access', 'max_edits_per_date': 'max_edits_per_date',
            'view_history_days': 'view_history_days', 'edit_history_days': 'edit_history_days',
        },
        'metrics': ('max_edits_per_date', 'view_history_days', 'edit_history_days'),
    },
    'class_attendance_edit_quotas': {
        'model': ClassTeacherEditQuota,
        'features': ('attendance_management',),
        'bounded_range_field': 'date',
        'fields': {
            'class_name': 'school_class__name', 'section': 'school_class__section',
            'date': 'date', 'teacher_edit_count': 'teacher_edit_count',
            'last_edit_at': 'last_teacher_edit_at',
        },
        'metrics': ('teacher_edit_count',),
    },
    'leave_policy': {
        'model': LeavePolicy,
        'features': ('leave_management',),
        'fields': {
            'max_leaves_per_month': 'max_leaves_per_month',
            'max_leaves_per_week': 'max_leaves_per_week',
            'max_consecutive_days': 'max_consecutive_days',
            'allow_backdated': 'allow_backdated',
            'count_approved_only': 'count_approved_only',
            'count_working_days_only': 'count_working_days_only',
            'max_rejections_before_suspension': 'max_rejections_before_suspension',
            'suspension_days': 'suspension_days',
        },
        'metrics': (
            'max_leaves_per_month', 'max_leaves_per_week', 'max_consecutive_days',
            'max_rejections_before_suspension', 'suspension_days',
        ),
    },
    'leave_suspensions': {
        'model': LeaveSuspension,
        'features': ('leave_management',),
        'fields': {
            'staff_name': 'staff__full_name', 'start_date': 'start_date',
            'end_date': 'end_date', 'is_active': 'is_active',
            'auto_triggered': 'auto_triggered',
        },
        'metrics': (),
    },
    'school_fee_settings': {
        'model': SchoolFeeSettings,
        'features': ('fee_settings',),
        'fields': {
            'fee_generation_day': 'fee_generation_day', 'due_date_offset': 'due_date_offset',
            'late_fee_penalty': 'late_fee_penalty', 'automation_enabled': 'automation_enabled',
        },
        'metrics': ('fee_generation_day', 'due_date_offset', 'late_fee_penalty'),
    },
    'fee_generation_runs': {
        'model': ManualGenerationLog,
        'features': ('fee_collection',),
        'fields': {
            'month': 'month', 'year': 'year', 'created_count': 'created_count',
            'skipped_existing': 'skipped_existing', 'skipped_no_fee': 'skipped_no_fee',
            'generated_at': 'generated_at', 'log_type': 'log_type',
        },
        'metrics': ('created_count', 'skipped_existing', 'skipped_no_fee'),
    },
    'product_categories': {
        'model': ProductCategory,
        'features': ('stock_management',),
        'fields': {'name': 'name', 'description': 'description'},
        'metrics': (),
    },
    'notifications': {
        'model': Notification,
        'features': ('dashboard',),
        'fields': {
            'message': 'message', 'link': 'link', 'is_read': 'is_read',
            'created_at': 'created_at',
        },
        'metrics': (),
        'guidance': 'Notification extra_data is not exposed; messages and links are tenant-local but may contain operational details.',
    },
    'fee_structures': {
        'model': FeeStructure,
        'features': ('fee_structure',),
        'fields': {'grade': 'grade', 'monthly_fee': 'monthly_fee'},
        'metrics': ('monthly_fee',),
    },
}

FILTER_OPERATORS = {'eq', 'contains', 'gt', 'gte', 'lt', 'lte', 'isnull'}
OPERATIONS = {'count', 'sum', 'average', 'group_count', 'list'}


def _expand_dataset_fields():
    numeric_types = {
        'BigIntegerField', 'DecimalField', 'FloatField', 'IntegerField',
        'PositiveBigIntegerField', 'PositiveIntegerField',
        'PositiveSmallIntegerField', 'SmallIntegerField',
    }
    excluded_types = {'BinaryField', 'FileField', 'ImageField'}
    for dataset in DATASETS.values():
        metrics = set(dataset['metrics'])
        for model_field in dataset['model']._meta.concrete_fields:
            field_type = model_field.get_internal_type()
            if field_type in excluded_types:
                continue
            dataset['fields'].setdefault(model_field.name, model_field.name)
            if (
                field_type in numeric_types
                and not model_field.primary_key
                and not model_field.is_relation
            ):
                metrics.add(model_field.name)
        dataset['metrics'] = tuple(sorted(metrics))


_expand_dataset_fields()


def _resolve_model_field(model, field_path):
    current_model = model
    resolved = None
    for part in field_path.split('__'):
        resolved = current_model._meta.get_field(part)
        if resolved.is_relation:
            current_model = resolved.related_model
    return resolved


def _coerce_filter_value(value, model_field, operator):
    if not isinstance(value, str) or len(value) > 120:
        raise ValueError('Filter values must be text no longer than 120 characters.')
    if operator == 'isnull':
        if value.lower() not in {'true', 'false'}:
            raise ValueError('isnull filters must be true or false.')
        return value.lower() == 'true'
    field_type = model_field.get_internal_type()
    if operator == 'contains':
        if field_type not in {'CharField', 'TextField', 'EmailField'}:
            raise ValueError('The contains operator is only available for text fields.')
        return value
    if field_type in {'DateField'}:
        try:
            parsed = date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError('Dates must use YYYY-MM-DD format.') from exc
        if parsed.isoformat() != value:
            raise ValueError('Dates must use YYYY-MM-DD format.')
        return parsed
    if field_type in {
        'IntegerField', 'PositiveIntegerField', 'SmallIntegerField',
        'PositiveSmallIntegerField', 'BigIntegerField', 'PositiveBigIntegerField',
    }:
        try:
            return int(value)
        except ValueError as exc:
            raise ValueError('This filter requires a whole number.') from exc
    if field_type in {'DecimalField', 'FloatField'}:
        try:
            parsed = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError('This filter requires a number.') from exc
        if not parsed.is_finite():
            raise ValueError('This filter requires a finite number.')
        return parsed
    if field_type == 'BooleanField':
        if value.lower() not in {'true', 'false'}:
            raise ValueError('Boolean filters must be true or false.')
        return value.lower() == 'true'
    return value


def _validated_fields(dataset, values, key, required=False, max_items=8):
    if values is None and not required:
        return []
    if not isinstance(values, list) or len(values) > max_items:
        raise ValueError(f'{key} must be a list of up to {max_items} fields.')
    allowed = dataset['fields']
    if required and not values:
        raise ValueError(f'{key} must include at least one field.')
    for value in values:
        if not isinstance(value, str) or value not in allowed:
            raise ValueError(f'Unsupported {key} field.')
    if len(values) != len(set(values)):
        raise ValueError(f'{key} must not contain duplicate fields.')
    return values


def _validate_bounded_date_range(dataset, filters, operation='list'):
    field_name = dataset.get('bounded_range_field')
    if not field_name:
        return
    bounds = {
        item['operator']: item['value']
        for item in filters
        if item.get('field') == field_name and item.get('operator') in {'gte', 'lte'}
    }
    if not bounds and operation != 'list':
        return
    if set(bounds) != {'gte', 'lte'}:
        raise ValueError(
            f"Queries for this dataset require both gte and lte date filters on {field_name}."
        )
    start_date = _coerce_filter_value(bounds['gte'], _resolve_model_field(dataset['model'], dataset['fields'][field_name]), 'gte')
    end_date = _coerce_filter_value(bounds['lte'], _resolve_model_field(dataset['model'], dataset['fields'][field_name]), 'lte')
    if end_date < start_date:
        raise ValueError('Date range end must not be before its start.')
    if operation == 'list' and (end_date - start_date).days > 365:
        raise ValueError('Date range cannot exceed 366 days.')


def _serialize_value(value):
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def _execute_school_data_query(
    dataset_name,
    operation,
    filters=None,
    metric='',
    group_by='',
    fields=None,
    limit=20,
    offset=0,
):
    if not isinstance(dataset_name, str):
        raise ValueError('Dataset must be text.')
    if dataset_name not in DATASETS:
        raise ValueError('Unknown school data dataset.')
    if not isinstance(operation, str):
        raise ValueError('Operation must be text.')
    if operation not in OPERATIONS:
        raise ValueError('Unknown query operation.')
    try:
        offset = int(offset)
    except (TypeError, ValueError) as exc:
        raise ValueError('offset must be a whole number.') from exc
    if offset < 0 or offset > 1_000_000:
        raise ValueError('offset must be between 0 and 1000000.')
    if operation != 'list' and offset:
        raise ValueError('offset is only supported for list queries.')
    dataset = DATASETS[dataset_name]
    model = dataset['model']
    queryset = model.objects.all()

    if filters is None:
        filters = []
    if not isinstance(filters, list) or len(filters) > 8:
        raise ValueError('Use no more than eight filters.')
    for item in filters:
        if not isinstance(item, dict) or set(item) != {'field', 'operator', 'value'}:
            raise ValueError('Each filter must contain field, operator, and value only.')
        field_name = item['field']
        operator = item['operator']
        if not isinstance(field_name, str) or not isinstance(operator, str):
            raise ValueError('Filter field and operator must be text.')
        if field_name not in dataset['fields']:
            raise ValueError('A filter field is not available in this dataset.')
        if operator not in FILTER_OPERATORS:
            raise ValueError('Unsupported filter operator.')
        model_path = dataset['fields'][field_name]
        model_field = _resolve_model_field(model, model_path)
        value = _coerce_filter_value(item['value'], model_field, operator)
        lookup = {'eq': 'exact', 'contains': 'icontains', 'isnull': 'isnull'}.get(operator, operator)
        queryset = queryset.filter(**{f'{model_path}__{lookup}': value})

    _validate_bounded_date_range(dataset, filters, operation=operation)

    if operation == 'count':
        return {'dataset': dataset_name, 'operation': operation, 'count': queryset.count()}

    if operation in {'sum', 'average'}:
        if metric not in dataset['metrics']:
            raise ValueError('The selected dataset does not support this metric.')
        model_path = dataset['fields'][metric]
        aggregate = Sum(model_path) if operation == 'sum' else Avg(model_path)
        result = queryset.aggregate(value=aggregate)['value']
        return {
            'dataset': dataset_name,
            'operation': operation,
            'metric': metric,
            'value': _serialize_value(result) if result is not None else None,
        }

    if operation == 'group_count':
        if not isinstance(group_by, str) or group_by not in dataset['fields']:
            raise ValueError('Choose a valid group_by field for this dataset.')
        model_path = dataset['fields'][group_by]
        rows = list(
            queryset.values(model_path).annotate(count=Count('pk'))
            .order_by('-count', model_path)[:21]
        )
        truncated = len(rows) > 20
        rows = rows[:20]
        return {
            'dataset': dataset_name,
            'operation': operation,
            'group_by': group_by,
            'rows': [
                {'value': _serialize_value(row[model_path]), 'count': row['count']}
                for row in rows
            ],
            'truncated': truncated,
        }

    selected_fields = _validated_fields(dataset, fields, 'fields', required=True)
    try:
        limit = max(1, min(int(limit), 25))
    except (TypeError, ValueError):
        limit = 20
    values = {name: F(dataset['fields'][name]) for name in selected_fields}
    rows = list(queryset.order_by('pk').values(**values)[offset:offset + limit + 1])
    truncated = len(rows) > limit
    rows = rows[:limit]
    return {
        'dataset': dataset_name,
        'operation': operation,
        'rows': [
            {key: _serialize_value(value) for key, value in row.items()}
            for row in rows
        ],
        'truncated': truncated,
        'limit': limit,
        'offset': offset,
        'next_offset': offset + limit if truncated else None,
    }


def query_school_data(
    schema_name,
    dataset_name,
    operation,
    filters=None,
    metric='',
    group_by='',
    fields=None,
    limit=20,
    offset=0,
):
    """Execute the query and force all database evaluation inside one tenant schema."""
    with schema_context(schema_name):
        return _execute_school_data_query(
            dataset_name,
            operation,
            filters=filters,
            metric=metric,
            group_by=group_by,
            fields=fields,
            limit=limit,
            offset=offset,
        )