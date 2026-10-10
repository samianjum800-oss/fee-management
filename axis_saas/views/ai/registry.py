"""Allow-listed, feature-gated assistant tool registry."""

import json
from copy import deepcopy
from datetime import date

from django.conf import settings

from .tools import (
    attendance_today_summary,
    attendance_range_summary,
    count_students,
    fee_collection_summary,
    leave_request_summary,
    lookup_staff,
    lookup_students,
    search_classes,
    search_defaulters,
    staff_attendance_summary,
    stock_summary,
    student_fee_balance,
)
from .query import DATASETS, FILTER_OPERATORS, OPERATIONS, query_school_data


TOOL_DEFINITIONS = {
    'query_school_data': {
        'feature': 'ai_assistant',
            'description': 'Query school records using the listed tenant datasets and fields. Use count, sum, average, group_count, or list. Aggregates may cover all-time data or use date filters. Large list queries require inclusive date bounds of at most 366 days and may be paged with offset. Never infer data that was not returned.',
        'parameters': {
            'type': 'object', 'properties': {
                'dataset': {'type': 'string', 'enum': sorted(DATASETS)},
                'operation': {'type': 'string', 'enum': sorted(OPERATIONS)},
                'filters': {
                    'type': 'array', 'maxItems': 8,
                    'items': {'type': 'object', 'properties': {
                        'field': {'type': 'string', 'enum': sorted({
                            field for dataset in DATASETS.values() for field in dataset['fields']
                        })},
                        'operator': {'type': 'string', 'enum': sorted(FILTER_OPERATORS)},
                        'value': {'type': 'string', 'maxLength': 120},
                    }, 'required': ['field', 'operator', 'value'], 'additionalProperties': False},
                },
                'metric': {'type': 'string', 'enum': sorted({
                    field for dataset in DATASETS.values() for field in dataset['metrics']
                })},
                'group_by': {'type': 'string', 'enum': sorted({
                    field for dataset in DATASETS.values() for field in dataset['fields']
                })},
                'fields': {
                    'type': 'array', 'maxItems': 8,
                    'items': {'type': 'string', 'enum': sorted({
                        field for dataset in DATASETS.values() for field in dataset['fields']
                    })},
                },
                'limit': {'type': 'integer', 'minimum': 1, 'maximum': 25},
                'offset': {'type': 'integer', 'minimum': 0, 'maximum': 1000000},
            }, 'required': ['dataset', 'operation'], 'additionalProperties': False,
        },
    },
    'search_students': {
        'feature': 'students',
        'description': 'Search this school only for students by name or exact roll number. Use for a student-name query or request for student records.',
        'parameters': {
            'type': 'object', 'properties': {
                'query': {'type': 'string', 'description': 'Student name or roll number.'},
                'limit': {'type': 'integer', 'minimum': 1, 'maximum': 10},
            }, 'required': ['query'], 'additionalProperties': False,
        },
    },
    'count_students': {
        'feature': 'students',
        'description': 'Count students, optionally filtered by exact grade, section, and active/suspended/graduated status.',
        'parameters': {
            'type': 'object', 'properties': {
                'grade': {'type': 'string', 'maxLength': 50},
                'section': {'type': 'string', 'maxLength': 50},
                'status': {'type': 'string', 'enum': ['active', 'suspended', 'graduated']},
            }, 'additionalProperties': False,
        },
    },
    'search_staff': {
        'feature': 'staff_management',
        'description': 'Search active staff in this school by name or staff ID.',
        'parameters': {
            'type': 'object', 'properties': {
                'query': {'type': 'string', 'description': 'Staff name or staff ID.'},
                'limit': {'type': 'integer', 'minimum': 1, 'maximum': 10},
            }, 'required': ['query'], 'additionalProperties': False,
        },
    },
    'student_fee_balance': {
        'feature': 'students',
        'extra_features': ('fee_collection', 'defaulters', 'reports'),
        'description': 'Read current pending fee balance for matching students. Use for a named student balance question only.',
        'parameters': {
            'type': 'object', 'properties': {
                'query': {'type': 'string', 'description': 'Student name or roll number.'},
                'limit': {'type': 'integer', 'minimum': 1, 'maximum': 10},
            }, 'required': ['query'], 'additionalProperties': False,
        },
    },
    'attendance_today': {
        'feature': 'attendance_management',
        'description': "Summarize this school's current-date full-day student attendance. Period marks are excluded.",
        'parameters': {'type': 'object', 'properties': {}, 'additionalProperties': False},
    },
    'attendance_range': {
        'feature': 'attendance_management',
        'description': 'Summarize recorded full-day attendance marks for an inclusive date range. Counts are attendance marks, not unique students; period marks are excluded.',
        'parameters': {
            'type': 'object', 'properties': {
                'start_date': {'type': 'string', 'format': 'date', 'description': 'Inclusive start date in YYYY-MM-DD format.'},
                'end_date': {'type': 'string', 'format': 'date', 'description': 'Inclusive end date in YYYY-MM-DD format.'},
            }, 'required': ['start_date', 'end_date'], 'additionalProperties': False,
        },
    },
    'fee_collection_summary': {
        'feature': 'fee_collection',
        'description': 'Summarize payment transactions in an inclusive date range and report the current outstanding balance separately. Range is limited to 366 days.',
        'parameters': {
            'type': 'object', 'properties': {
                'start_date': {'type': 'string', 'format': 'date'},
                'end_date': {'type': 'string', 'format': 'date'},
            }, 'required': ['start_date', 'end_date'], 'additionalProperties': False,
        },
    },
    'staff_attendance_range': {
        'feature': 'reports',
        'description': 'Summarize staff attendance entries for an inclusive date range. Holidays and weekends are excluded from the working-day rate denominator. Range is limited to 366 days.',
        'parameters': {
            'type': 'object', 'properties': {
                'start_date': {'type': 'string', 'format': 'date'},
                'end_date': {'type': 'string', 'format': 'date'},
            }, 'required': ['start_date', 'end_date'], 'additionalProperties': False,
        },
    },
    'leave_request_summary': {
        'feature': 'leave_management',
        'description': 'Count staff leave requests created in an inclusive date range, grouped by pending, approved, rejected, and cancelled status. Range is limited to 366 days.',
        'parameters': {
            'type': 'object', 'properties': {
                'start_date': {'type': 'string', 'format': 'date'},
                'end_date': {'type': 'string', 'format': 'date'},
            }, 'required': ['start_date', 'end_date'], 'additionalProperties': False,
        },
    },
    'search_classes': {
        'feature': 'classes_management',
        'description': 'Find active classes, sections or wings and link to their class detail pages.',
        'parameters': {
            'type': 'object', 'properties': {
                'query': {'type': 'string', 'description': 'Class, section, campus or wing name.'},
                'limit': {'type': 'integer', 'minimum': 1, 'maximum': 10},
            }, 'required': ['query'], 'additionalProperties': False,
        },
    },
    'search_defaulters': {
        'feature': 'defaulters',
        'description': 'Read the highest current fee balances, optionally filtered by student name or roll number.',
        'parameters': {
            'type': 'object', 'properties': {
                'query': {'type': 'string', 'description': 'Optional student name or roll number.'},
                'limit': {'type': 'integer', 'minimum': 1, 'maximum': 10},
            }, 'additionalProperties': False,
        },
    },
    'stock_summary': {
        'feature': 'stock_management',
        'description': 'Read product count, current unit count and low-stock products for this school.',
        'parameters': {'type': 'object', 'properties': {}, 'additionalProperties': False},
    },
}


def _query_datasets_for_tenant(tenant):
    return [
        name for name, dataset in DATASETS.items()
        if all(tenant.is_feature_enabled(feature, 'desktop') for feature in dataset['features'])
    ]


def enabled_tool_definitions(tenant, *, consent_confirmed=False):
    if not getattr(settings, 'AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER', False):
        return []
    if not consent_confirmed:
        return []
    definitions = []
    for name, definition in TOOL_DEFINITIONS.items():
        if name == 'query_school_data':
            if not tenant.is_feature_enabled('ai_assistant', 'desktop'):
                continue
            available_datasets = _query_datasets_for_tenant(tenant)
            if not available_datasets:
                continue
            scoped = deepcopy(definition)
            scoped['parameters']['properties']['dataset']['enum'] = available_datasets
            allowed_fields = sorted({
                field for dataset_name in available_datasets
                for field in DATASETS[dataset_name]['fields']
            })
            allowed_metrics = sorted({
                field for dataset_name in available_datasets
                for field in DATASETS[dataset_name]['metrics']
            })
            scoped['parameters']['properties']['filters']['items']['properties']['field']['enum'] = allowed_fields
            scoped['parameters']['properties']['group_by']['enum'] = allowed_fields
            scoped['parameters']['properties']['fields']['items']['enum'] = allowed_fields
            scoped['parameters']['properties']['metric']['enum'] = allowed_metrics
            description = []
            for dataset_name in available_datasets:
                dataset = DATASETS[dataset_name]
                description.append(
                    f"{dataset_name} ({', '.join(dataset['fields'])}); "
                    f"sum/average metrics: {', '.join(dataset['metrics']) or 'none'}"
                    + (f"; {dataset['guidance']}" if dataset.get('guidance') else '')
                )
            scoped['description'] += ' Available datasets and safe fields: ' + '; '.join(description) + '.'
            definitions.append({
                'type': 'function',
                'function': {
                    'name': name,
                    'description': scoped['description'],
                    'parameters': scoped['parameters'],
                },
            })
            continue
        if not tenant.is_feature_enabled(definition['feature'], 'desktop'):
            continue
        if definition.get('required_features') and not all(
            tenant.is_feature_enabled(feature, 'desktop')
            for feature in definition['required_features']
        ):
            continue
        if definition.get('extra_features') and not any(
            tenant.is_feature_enabled(feature, 'desktop')
            for feature in definition['extra_features']
        ):
            continue
        definitions.append({
            'type': 'function',
            'function': {
                'name': name,
                'description': definition['description'],
                'parameters': definition['parameters'],
            },
        })
    return definitions


def _text_argument(arguments, key, max_length=80, required=True):
    value = arguments.get(key, '')
    if not isinstance(value, str):
        raise ValueError(f'{key} must be text')
    value = value.strip()
    if required and len(value) < 2:
        raise ValueError(f'{key} must contain at least 2 characters')
    if len(value) > max_length:
        raise ValueError(f'{key} is too long')
    return value


def _limit_argument(arguments, default=8):
    try:
        value = int(arguments.get('limit', default))
    except (TypeError, ValueError):
        return default
    return max(1, min(value, 10))


def _date_range_arguments(arguments, subject):
    try:
        start_text = _text_argument(arguments, 'start_date', max_length=10)
        end_text = _text_argument(arguments, 'end_date', max_length=10)
        start_date = date.fromisoformat(start_text)
        end_date = date.fromisoformat(end_text)
    except ValueError as exc:
        raise ValueError(f'{subject} dates must use YYYY-MM-DD format.') from exc
    if start_date.isoformat() != start_text or end_date.isoformat() != end_text:
        raise ValueError(f'{subject} dates must use YYYY-MM-DD format.')
    if end_date < start_date:
        raise ValueError(f'{subject} end date must not be before the start date.')
    if (end_date - start_date).days > 365:
        raise ValueError(f'{subject} date range cannot exceed 366 days.')
    return start_date, end_date


def execute_tool(
    name,
    raw_arguments,
    *,
    tenant,
    schema_name,
    roman_urdu=False,
    pages=(),
    consent_confirmed=False,
):
    """Execute one allow-listed tool against the resolved tenant schema."""
    if not getattr(settings, 'AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER', False):
        raise PermissionError('External school-data tools are disabled by deployment policy.')
    if not consent_confirmed:
        raise PermissionError('The school administrator has not consented for this chat.')
    if name not in TOOL_DEFINITIONS:
        raise ValueError('Unknown assistant tool')
    definition = TOOL_DEFINITIONS[name]
    if not tenant.is_feature_enabled(definition['feature'], 'desktop'):
        raise PermissionError('This school feature is not enabled.')
    if definition.get('required_features') and not all(
        tenant.is_feature_enabled(feature, 'desktop')
        for feature in definition['required_features']
    ):
        raise PermissionError('This school feature is not enabled.')

    if not isinstance(raw_arguments, str) or len(raw_arguments) > 12000:
        raise ValueError('Tool arguments must be text no longer than 12000 characters.')
    if definition.get('extra_features') and not any(
        tenant.is_feature_enabled(feature, 'desktop')
        for feature in definition['extra_features']
    ):
        raise PermissionError('Fee records are not enabled for this school.')

    try:
        arguments = json.loads(raw_arguments or '{}')
    except (TypeError, ValueError) as exc:
        raise ValueError('Tool arguments were not valid JSON') from exc
    if not isinstance(arguments, dict):
        raise ValueError('Tool arguments must be an object')

    if name == 'query_school_data':
        dataset_name = arguments.get('dataset')
        if dataset_name not in DATASETS:
            raise ValueError('Unknown school data dataset.')
        dataset = DATASETS[dataset_name]
        if not all(tenant.is_feature_enabled(feature, 'desktop') for feature in dataset['features']):
            raise PermissionError('This school module is not enabled.')
        return query_school_data(
            schema_name,
            dataset_name,
            arguments.get('operation'),
            filters=arguments.get('filters'),
            metric=arguments.get('metric', ''),
            group_by=arguments.get('group_by', ''),
            fields=arguments.get('fields'),
            limit=arguments.get('limit', 20),
            offset=arguments.get('offset', 0),
        )

    if name == 'search_students':
        return lookup_students(
            schema_name,
            _text_argument(arguments, 'query'),
            roman_urdu=roman_urdu,
            limit=_limit_argument(arguments),
        )
    if name == 'count_students':
        grade = _text_argument(arguments, 'grade', max_length=50, required=False)
        section = _text_argument(arguments, 'section', max_length=50, required=False)
        status = _text_argument(arguments, 'status', max_length=20, required=False)
        if status and status not in {'active', 'suspended', 'graduated'}:
            raise ValueError('Unknown student status.')
        return count_students(
            schema_name,
            roman_urdu=roman_urdu,
            grade=grade,
            section=section,
            status=status,
        )
    if name == 'search_staff':
        return lookup_staff(
            schema_name,
            _text_argument(arguments, 'query'),
            roman_urdu=roman_urdu,
            limit=_limit_argument(arguments),
        )
    if name == 'student_fee_balance':
        return student_fee_balance(
            schema_name,
            _text_argument(arguments, 'query'),
            roman_urdu=roman_urdu,
            limit=_limit_argument(arguments),
        )
    if name == 'attendance_today':
        attendance_page = next((page for page in pages if page['key'] == 'attendance_report'), None)
        return attendance_today_summary(
            schema_name,
            roman_urdu=roman_urdu,
            report_url=attendance_page['url'] if attendance_page else None,
        )
    if name == 'attendance_range':
        start_date, end_date = _date_range_arguments(arguments, 'Attendance')
        attendance_page = next((page for page in pages if page['key'] == 'attendance_report'), None)
        return attendance_range_summary(
            schema_name,
            start_date,
            end_date,
            roman_urdu=roman_urdu,
            report_url=attendance_page['url'] if attendance_page else None,
        )
    if name == 'fee_collection_summary':
        start_date, end_date = _date_range_arguments(arguments, 'Fee collection')
        return fee_collection_summary(
            schema_name, start_date, end_date, roman_urdu=roman_urdu,
        )
    if name == 'staff_attendance_range':
        start_date, end_date = _date_range_arguments(arguments, 'Staff attendance')
        return staff_attendance_summary(
            schema_name, start_date, end_date, roman_urdu=roman_urdu,
        )
    if name == 'leave_request_summary':
        start_date, end_date = _date_range_arguments(arguments, 'Leave request')
        return leave_request_summary(
            schema_name, start_date, end_date, roman_urdu=roman_urdu,
        )
    if name == 'search_classes':
        return search_classes(
            schema_name,
            _text_argument(arguments, 'query'),
            roman_urdu=roman_urdu,
            limit=_limit_argument(arguments),
        )
    if name == 'search_defaulters':
        return search_defaulters(
            schema_name,
            _text_argument(arguments, 'query', required=False),
            roman_urdu=roman_urdu,
            limit=_limit_argument(arguments),
        )
    if name == 'stock_summary':
        return stock_summary(schema_name, roman_urdu=roman_urdu)
    raise ValueError('Tool is not implemented')
