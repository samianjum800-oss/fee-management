"""Read-only, tenant-scoped tools available to the admin assistant."""

from difflib import get_close_matches
import re
import unicodedata

from django.db.models import Count, Q, Sum
from django.urls import reverse
from django.utils.http import urlencode
from django.utils import timezone
from django_tenants.utils import schema_context

from ...models import Product, SchoolClass, Staff, Student, StudentAttendance
from ..helpers import get_student_pending_queryset


def _normalized_name(value):
    value = unicodedata.normalize('NFKD', value or '').encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', ' ', value.lower()).strip()


def _fuzzy_student_names(schema_name, query, limit):
    """Use a bounded same-schema candidate set only when exact search is empty."""
    normalized_query = _normalized_name(query)
    if len(normalized_query) < 4:
        return []
    with schema_context(schema_name):
        names = list(
            Student.objects.filter(status='active')
            .exclude(name='')
            .values_list('name', flat=True)
            .distinct()[:3000]
        )
    normalized_to_names = {}
    for candidate in names:
        normalized_to_names.setdefault(_normalized_name(candidate), []).append(candidate)
    close = get_close_matches(normalized_query, list(normalized_to_names), n=limit, cutoff=0.72)
    return [name for match in close for name in normalized_to_names[match]]


def lookup_students(schema_name, name, roman_urdu=True, limit=8):
    """Search only this tenant's student table and return profile links."""
    name = (name or '').strip()[:80]
    limit = max(1, min(int(limit), 10))
    if len(name) < 2:
        return {
            'reply': 'Student ka naam thora aur specific likhein.' if roman_urdu else 'Please enter at least two characters of the student name.',
            'actions': [],
        }

    with schema_context(schema_name):
        matches = Student.objects.filter(
            Q(name__icontains=name) | Q(roll_number__iexact=name)
        ).order_by('name', 'roll_number')
        total = matches.count()
        students = list(matches[:limit])
        if total == 0:
            fuzzy_names = _fuzzy_student_names(schema_name, name, limit)
            if fuzzy_names:
                fuzzy_matches = Student.objects.filter(
                    status='active', name__in=fuzzy_names
                ).order_by('name', 'roll_number')
                total = fuzzy_matches.count()
                students = list(fuzzy_matches[:limit])
        actions = [{
            'label': f'{student.name} · {student.roll_number}',
            'detail': f'{student.grade} · {student.section}',
            'url': reverse('student_profile', kwargs={
                'schema_name': schema_name,
                'student_id': student.pk,
            }),
        } for student in students]

    if total > len(students):
        student_list_url = reverse('student_list', kwargs={'schema_name': schema_name})
        actions.append({
            'label': 'Baaki results dekhein' if roman_urdu else 'View all matching students',
            'detail': f'{total} total matches',
            'url': f'{student_list_url}?{urlencode({"q": name})}',
        })

    if roman_urdu:
        reply = f'{name} naam se {total} student' + (' mile.' if total == 1 else 's mile.')
    else:
        reply = f'Found {total} student' + (' matching' if total == 1 else 's matching') + f' “{name}”.'
    return {'reply': reply, 'actions': actions}


def count_students(schema_name, roman_urdu=True):
    with schema_context(schema_name):
        total = Student.objects.count()
        active = Student.objects.filter(status='active').count()
    if roman_urdu:
        reply = f'School mein kul {total} students hain; in mein se {active} active hain.'
    else:
        reply = f'The school has {total} students, including {active} active students.'
    return {
        'reply': reply,
        'actions': [{
            'label': 'Students list',
            'detail': 'School ke student records dekhein.' if roman_urdu else 'Browse student records.',
            'url': reverse('student_list', kwargs={'schema_name': schema_name}),
        }],
    }


def lookup_staff(schema_name, name, roman_urdu=True, limit=8):
    name = (name or '').strip()[:80]
    limit = max(1, min(int(limit), 10))
    with schema_context(schema_name):
        matches = Staff.objects.filter(status='active').filter(
            Q(full_name__icontains=name) | Q(staff_id__iexact=name)
        ).order_by('full_name')
        total = matches.count()
        staff_members = list(matches[:limit])
    actions = [{
        'label': member.full_name,
        'detail': f'{member.job_title} · {member.staff_id}',
        'url': reverse('staff_profile', kwargs={
            'schema_name': schema_name,
            'staff_id': member.pk,
        }),
    } for member in staff_members]
    if roman_urdu:
        reply = f'{name} se match karte hue {total} active staff mile.'
    else:
        reply = f'Found {total} active staff member(s) matching “{name}”.'
    return {'reply': reply, 'actions': actions}


def student_fee_balance(schema_name, name, roman_urdu=True, limit=8):
    name = (name or '').strip()[:80]
    limit = max(1, min(int(limit), 10))
    with schema_context(schema_name):
        students = get_student_pending_queryset(
            Student.objects.filter(
                Q(name__icontains=name) | Q(roll_number__iexact=name)
            ).order_by('name')
        )
        matches = list(students[:limit])
        total = students.count()
    actions = [{
        'label': f'{student.name} · {student.roll_number}',
        'detail': f'{student.pending_amount:,.2f} pending · {student.grade} · {student.section}',
        'url': reverse('student_profile', kwargs={
            'schema_name': schema_name,
            'student_id': student.pk,
        }),
    } for student in matches]
    if roman_urdu:
        reply = f'{name} ke {total} matching student record(s) mile. Profile links par current pending balance diya hai.'
    else:
        reply = f'Found {total} matching student record(s). Current pending balances are shown on their profile links.'
    return {'reply': reply, 'actions': actions}


def attendance_today_summary(schema_name, roman_urdu=True, report_url=None):
    today = timezone.localdate()
    with schema_context(schema_name):
        records = StudentAttendance.objects.filter(
            date=today,
            period_order__isnull=True,
        )
        totals = {
            'marked': records.count(),
            'present': records.filter(status='present').count(),
            'absent': records.filter(status='absent').count(),
            'late': records.filter(status='late').count(),
            'half_day': records.filter(status='half_day').count(),
            'excused': records.filter(status='excused').count(),
        }
        totals['active_students'] = Student.objects.filter(status='active').count()
    eligible = totals['present'] + totals['absent'] + totals['late'] + totals['half_day']
    rate = round((totals['present'] + totals['late'] + totals['half_day']) * 100 / eligible, 1) if eligible else 0
    if roman_urdu:
        reply = (
            f'Aaj full-day attendance: {totals["marked"]} marks, {totals["present"]} present, '
            f'{totals["absent"]} absent, {totals["late"]} late; recorded attendance rate {rate}%. '
            f'{totals["active_students"]} active students hain.'
        )
    else:
        reply = (
            f"Today's full-day attendance: {totals['marked']} marks, {totals['present']} present, "
            f"{totals['absent']} absent, {totals['late']} late; recorded attendance rate {rate}%. "
            f"There are {totals['active_students']} active students."
        )
    actions = []
    if report_url:
        actions.append({
            'label': 'Attendance report',
            'detail': today.isoformat(),
            'url': report_url,
        })
    return {'reply': reply, 'actions': actions}


def search_defaulters(schema_name, query='', roman_urdu=True, limit=8):
    query = (query or '').strip()[:80]
    with schema_context(schema_name):
        students = Student.objects.filter(status='active')
        if query:
            students = students.filter(
                Q(name__icontains=query) | Q(roll_number__iexact=query)
            )
        students = get_student_pending_queryset(students).filter(
            pending_amount__gt=0
        ).order_by('-pending_amount', 'name')
        total = students.count()
        matches = list(students[:max(1, min(limit, 10))])
    actions = [{
        'label': f'{student.name} · {student.roll_number}',
        'detail': f'{student.pending_amount:,.2f} pending · {student.grade} · {student.section}',
        'url': reverse('student_profile', kwargs={
            'schema_name': schema_name,
            'student_id': student.pk,
        }),
    } for student in matches]
    if roman_urdu:
        reply = f'{total} active student(s) ki fee pending hai.'
    else:
        reply = f'{total} active student(s) have a pending fee balance.'
    return {'reply': reply, 'actions': actions}


def search_classes(schema_name, query, roman_urdu=True, limit=8):
    query = (query or '').strip()[:80]
    with schema_context(schema_name):
        classes = SchoolClass.objects.filter(is_active=True).select_related(
            'wing_category', 'wing_category__parent', 'class_teacher'
        ).annotate(active_students=Count('students', filter=Q(students__status='active')))
        if query:
            classes = classes.filter(
                Q(name__icontains=query)
                | Q(section__icontains=query)
                | Q(wing_category__name__icontains=query)
                | Q(wing_category__parent__name__icontains=query)
            )
        total = classes.count()
        matches = list(classes.order_by('name', 'section')[:max(1, min(limit, 10))])
    actions = [{
        'label': str(school_class),
        'detail': f'{school_class.active_students} active students · {school_class.class_teacher.full_name if school_class.class_teacher else "No class teacher"}',
        'url': reverse('class_detailed', kwargs={
            'schema_name': schema_name,
            'class_id': school_class.pk,
        }),
    } for school_class in matches]
    reply = (
        f'{total} matching class(es) milin.' if roman_urdu
        else f'Found {total} matching class(es).'
    )
    return {'reply': reply, 'actions': actions}


def stock_summary(schema_name, roman_urdu=True):
    with schema_context(schema_name):
        total_products = Product.objects.count()
        total_units = Product.objects.aggregate(total=Sum('quantity'))['total'] or 0
        low_stock = list(
            Product.objects.filter(quantity__lte=5).order_by('quantity', 'name')[:8]
        )
    actions = [{
        'label': product.name,
        'detail': f'{product.quantity} units left · SKU {product.sku}',
        'url': reverse('product_detail', kwargs={
            'schema_name': schema_name,
            'product_id': product.pk,
        }),
    } for product in low_stock]
    reply = (
        f'{total_products} products aur {total_units} units current stock mein hain. '
        f'{len(low_stock)} products mein 5 ya us se kam units hain.'
        if roman_urdu else
        f'{total_products} products and {total_units} units are in stock. '
        f'{len(low_stock)} products have five or fewer units.'
    )
    return {'reply': reply, 'actions': actions}
