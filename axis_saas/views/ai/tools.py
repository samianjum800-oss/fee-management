"""Read-only, tenant-scoped tools available to the admin assistant."""

from django.db.models import Q
from django.urls import reverse
from django.utils.http import urlencode
from django_tenants.utils import schema_context

from ...models import Student


def lookup_students(schema_name, name, roman_urdu=True):
    """Search only this tenant's student table and return profile links."""
    name = (name or '').strip()[:80]
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
        students = list(matches[:8])
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
