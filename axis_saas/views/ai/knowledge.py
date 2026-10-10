"""Feature-aware admin page knowledge for the AXIS assistant."""

from django.urls import NoReverseMatch, reverse


PAGE_CATALOG = (
    {
        'key': 'dashboard',
        'label': 'Dashboard',
        'route': 'dashboard',
        'features': ('dashboard',),
        'aliases': ('dashboard', 'home', 'overview', 'main page'),
        'description': 'School-wide overview and operational summaries.',
    },
    {
        'key': 'students',
        'label': 'Students',
        'route': 'student_list',
        'features': ('students',),
        'aliases': ('student', 'students', 'talib', 'taliba', 'student list'),
        'description': 'Search students and open their profiles.',
    },
    {
        'key': 'staff',
        'label': 'Staff management',
        'route': 'staff_list',
        'features': ('staff_management',),
        'aliases': ('staff', 'teacher', 'teachers', 'ustad', 'staff management'),
        'description': 'Review staff accounts, attendance and profiles.',
    },
    {
        'key': 'attendance',
        'label': 'Attendance management',
        'route': 'admin_attendance',
        'features': ('attendance_management',),
        'aliases': ('attendance', 'hazri', 'hajri', 'attendance management', 'mark attendance'),
        'description': 'Mark and review class attendance.',
    },
    {
        'key': 'attendance_report',
        'label': 'Attendance report',
        'route': 'attendance_report',
        'features': ('reports', 'attendance_management'),
        'aliases': ('attendance report', 'hazri report', 'hajri report'),
        'description': 'Compare attendance by campus, wing, class, section and student.',
    },
    {
        'key': 'reports',
        'label': 'School reports',
        'route': 'reports',
        'features': ('reports',),
        'aliases': ('report', 'reports', 'school report', 'financial report'),
        'description': 'Review finance, enrolment, staff, leave and inventory summaries.',
    },
    {
        'key': 'fees',
        'label': 'Fee collection',
        'route': 'fee_collection',
        'features': ('fee_collection',),
        'aliases': ('fee', 'fees', 'fee collection', 'collect fee', 'wasooli', 'jama'),
        'description': 'Find a student and record a fee payment.',
    },
    {
        'key': 'defaulters',
        'label': 'Fee defaulters',
        'route': 'defaulters',
        'features': ('defaulters',),
        'aliases': ('defaulter', 'defaulters', 'pending fee', 'overdue fee', 'baqaya'),
        'description': 'Review students with unpaid or partly paid fees.',
    },
    {
        'key': 'classes',
        'label': 'Classes and sections',
        'route': 'classes_management',
        'features': ('classes_management',),
        'aliases': ('class', 'classes', 'section', 'sections', 'jamaat'),
        'description': 'Browse classes, sections and class profiles.',
    },
    {
        'key': 'timetable',
        'label': 'Timetable',
        'route': 'timetable_management',
        'features': ('timetable_management',),
        'aliases': ('timetable', 'schedule', 'periods', 'period', 'waqt'),
        'description': 'Manage school calendars, periods and schedules.',
    },
    {
        'key': 'leave',
        'label': 'Leave management',
        'route': 'leave_management',
        'features': ('leave_management',),
        'aliases': ('leave', 'leaves', 'chutti', ' छुट्टी', 'leave management'),
        'description': 'Review and manage staff leave requests.',
    },
    {
        'key': 'stock',
        'label': 'Stock management',
        'route': 'stock_management',
        'features': ('stock_management',),
        'aliases': ('stock', 'inventory', 'product', 'products', 'maal'),
        'description': 'Review school inventory and product quantities.',
    },
    {
        'key': 'fee_structure',
        'label': 'Fee structure',
        'route': 'fee_structure',
        'features': ('fee_structure',),
        'aliases': ('fee structure', 'monthly fee', 'tuition fee'),
        'description': 'Review configured fees by grade.',
    },
)


def available_pages(tenant, schema_name):
    """Return only links that this tenant is allowed to access."""
    pages = []
    for page in PAGE_CATALOG:
        if not all(tenant.is_feature_enabled(feature, 'desktop') for feature in page['features']):
            continue
        try:
            url = reverse(page['route'], kwargs={'schema_name': schema_name})
        except NoReverseMatch:
            continue
        pages.append({**page, 'url': url})
    return pages
