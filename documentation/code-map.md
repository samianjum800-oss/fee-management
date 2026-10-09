# AXIS Code Map

Use this index to move from a behavior to its implementation owner. The route catalog in [API and Routes](api.md) is the authoritative registered path inventory. Migration filenames are chronological implementation history; old backup files are not active code.

## Root files

| Path | Role |
|---|---|
| `manage.py` | Django command-line entry point; sets `axis_saas.settings`. |
| `requirements.txt` | Python runtime dependencies and pins. |
| `runtime.txt` | Hosting runtime version declaration. |
| `Dockerfile` | Python 3.11 image, dependencies, static collection, startup entrypoint. |
| `start.sh` | Database wait, migrations, starter tenant creation, Gunicorn launch; see security caveat in Operations. |
| `README.md` | Short project overview only. |
| `data.sql`, `structure.sql` | Large SQL data/schema artifacts; not active Django migration source. |
| `back.py` | Interactive utility that fetches history and can `git reset --hard`; dangerous and unrelated to application startup. Do not use casually. |
| `g.py` | Patch/repair utility targeting `views/assign_teachers.py`; has write/compile logic. Not a runtime module. |
| `push.py` | Interactive helper that stages all changes, commits, and pushes to `main`; do not run without explicit review. |
| `g`, `logging`, `re` | Opaque/non-Django checked-in artifacts (plain text/PostScript according to file signatures); no known runtime import path. |

## Django package: `axis_saas/`

| File or package | Responsibility |
|---|---|
| `settings.py` | Environment, PostgreSQL, django-tenants, middleware, templates, static/media, Redis, CSRF and auth settings. |
| `public_urls.py` | Active root URLconf: public, tenant-admin and staff routes/wrappers. |
| `tenant_urls.py` | Small tenant URLconf subset; configured but not the active full route table under current path middleware. |
| `staff_urls.py` | Staff portal page/API route tree included at `/portal/staff/`. |
| `urls.py` | Small alternate route file; not selected by `ROOT_URLCONF`. |
| `models.py` | Tenant registry and primary school domain model definitions. |
| `biometric_models.py` | Public staff WebAuthn credential model. |
| `forms.py` | Student/staff/fee/class/subject forms and wing-aware selection logic. |
| `admin.py` | Django admin registrations/actions. |
| `apps.py` | App config; imports signals in `ready()`. |
| `signals.py` | Schema provisioning/password sync, cache invalidation, timetable reconcile, leave-attendance sync. |
| `context_processors.py` | Tenant fallback object and staff portal feature context. |
| `session_backend.py` | Database-backed session store that forces session CRUD into public schema. |
| `pwa_views.py` | Tenant-aware admin PWA manifest and root service worker response. |
| `asgi.py`, `wsgi.py` | ASGI and WSGI deployment entry points. |
| `__init__.py` | Package initialization. |
| `views.py` | Generated re-export shim; Python resolves `axis_saas.views` to the `views/` package in current layout. |
| `views_fix.py` | One-line historical fee-settings fix note; not an active view implementation. |
| `models.py.bak4`, `models.py.bak_dup`, `public_urls.py.bak_labels` | Historical snapshots; not imported by active settings. |
| `middleware/url_tenant_middleware.py` | Parses `/portal/<schema>/`, sets request tenant and database schema. |
| `middleware/staff_tenant_middleware.py` | Staff public-path allowlist, session-token validation, staff tenant/schema selection, biometric setup gate. |
| `middleware/__init__.py` | Middleware package marker. |

### View modules

`axis_saas/views/__init__.py` re-exports most split view modules for legacy imports. `public_urls.py` imports explicit callables from these owners.

| Module | Area |
|---|---|
| `dashboard.py` | Admin dashboard and aggregate context. |
| `helpers.py` | Shared fee, dashboard, cache, serialization, and feature helpers; high fan-in module, check callers before changing contracts. |
| `students.py` | Student CRUD/profile/search, fee/payment APIs, offline sync, teacher student list. |
| `fee_collection.py` | Payments, fee collection/receipt, fee list APIs and fee status/generation helpers. |
| `fee_structure.py` | Fee structure and voucher-generation settings/workflows. |
| `fee_settings.py` | Fee generation settings. |
| `fee_logs.py` | Fee-generation/payment logs and mobile variant. |
| `reports.py` | Defaulter and financial reports plus mobile forms. |
| `vouchers.py` | Voucher status, generation, listing, and HTML. |
| `stock.py` | Inventory/product/category pages and APIs. |
| `sell.py` | Separate product-sale workflow. |
| `notifications.py` | Admin notification APIs/dismissal. |
| `search.py` | Tenant-wide global search. |
| `settings.py` | Tenant school settings. |
| `staff.py` | Admin staff CRUD, search, credentials, status/logout/biometric controls. |
| `staff_extras.py` | Admin staff subject/class assignment APIs and quick stats. |
| `staff_portal.py` | Staff authentication, feature gating, dashboard/profile/classes/notifications. |
| `staff_portal_leave_management.py` | Staff leave application, policy, history, cancellation. |
| `staff_portal_leave_managemetn.py` | Misspelled backward-compatibility import shim. |
| `staff_biometric.py` | WebAuthn registration and login API. |
| `staff_pwa.py` | Staff manifest, scoped service worker and offline page. |
| `admin_attendence.py` | Admin attendance page and student/staff attendance/policy/audit APIs (filename spelling as in source). |
| `staff_attendence.py` | Staff attendance page and teacher permissions/marking/records APIs (filename spelling as in source). |
| `leave_management.py` | Admin staff leave, quotas/policy, approval, suspension and summary APIs. |
| `classes.py` | Class/subject CRUD, strength and class-teacher operations. |
| `class_staff.py` | Class-page staff assignment endpoints. |
| `class_teacher_views.py` | Class-teacher-facing page/view helpers. |
| `teachers_management.py` | Consolidated subjects, teaching assignments, class-teacher tabs; legacy class redirect. |
| `wing_classes.py`, `wing_class_detailed.py` | Wing-school class list/detail implementations. |
| `single_classes.py`, `single_class_detailed.py` | Single-school class list/detail implementations. |
| `timetable.py` | Calendar, day schedules, holidays, labels, period/timetable API functions. |
| `periods.py` | Period-block editor, timetable persistence/reconciliation, break controls. |
| `timetable_assignments.py` | Persisted timetable-to-class assignment. |
| `assign_teachers.py` | Period teacher grid, conflicts, leave lookup and substitute assignments. |
| `__init__.py` | Compatibility re-exports; not a route registry. |
| `timetable.py.bak`, `timetable.py.bak_dupmsg`, `timetable.py.bak_labels` | Historical timetable snapshots; not imported as active modules. |

### Shared utilities and template tags

| Path | Responsibility |
|---|---|
| `utils/attendance_auto_mark.py` | Idempotent past-attendance catch-up; skips holidays, treats approved student leave as excused, Redis lock limits to hourly per tenant. |
| `utils/class_display.py` | Safe wing-aware class/student display names, including graceful fallback for orphaned wing FKs. |
| `utils/display_grade.py` | Student display grade derived from class and wing. |
| `utils/__init__.py` | Utility package marker. |
| `templatetags/class_display.py` | Template-level class label filters/helpers. |
| `templatetags/fee_extras.py` | Fee template filters/tags. |
| `templatetags/__init__.py` | Template-tag package marker. |

## Migrations

`axis_saas/migrations/0001_initial.py` through `0036_class_timetable_assignment_multi.py` define and evolve schema. In order, the sequence covers initial tenant/fee structures, schema repair, biometric credentials, tenant types, wing/class structure, dropped legacy student field, academic calendar/timetable, day schedules/breaks/labels and uniqueness hardening, persisted timetable and teacher assignments, staff leave/suspensions, substitute assignments, biometric switch, leave hardening, period teacher audit, production attendance, attendance source values, class-teacher attendance permissions, audit indexes and multiple timetable assignments. There are migration files for every numbered migration from `0001` to `0036`; inspect exact dependencies/data operations before changing one. `migrations/__init__.py` is the package marker.

## Management commands

Every command name and one-line purpose is listed in [Operations](operations.md). Their source directory is `axis_saas/management/commands/`. The commands fall into these groups:

- **Attendance:** `attendance_auto_absent`, `attendance_auto_present`, `attendance_monthly_report`, `attendance_reminder`.
- **Fee automation/repair:** `apply_late_fees`, `auto_generate_fees`, `generate_monthly_fees`, `backfill_custom_fee`, `backfill_fee_structures`, `backfill_student_fees`, `fix_fee_data`, `repair_student_fees`, `recalc_fee_paid_amounts`, `check_payments`, `check_student_fees`, `check_cron`.
- **Tenant/schema repair and inspection:** `check_schema_columns`, `fix_dayschedule_columns`, `fix_missing_tables`, `fix_timetable_tables`, `inspect_tenant_schema`, `sync_all_schemas`.
- **Staff/leave and notifications:** `add_staff_feature_to_tenants`, `enable_leave_feature`, `expire_leave_suspensions`, `hash_existing_passwords`, `create_test_notification`, `list_notifications`.
- **Class maintenance:** `list_classes`, `normalize_class_data`.

These include mutating commands and overlapping repair utilities; they are operational tools, not safe startup hooks by default.

## Tests

Tests use Django's test framework. Existing modules:

| Test module | Main coverage |
|---|---|
| `tests/test_assign_teachers.py` | Teacher-grid assignments and behavior. |
| `tests/test_assign_teachers_hardening_v4.py` | Hardened assignment constraints/regressions. |
| `tests/test_assign_teachers_page.py` | Assignment page rendering. |
| `tests/test_attendance_system.py` | Admin/staff attendance, permissions, edit quota, holidays, audits, leave, tenant isolation. |
| `tests/test_dashboard.py`, `tests/test_dashboard_v3.py` | Dashboard context/aggregation/cache regressions. |
| `tests/test_leave_management.py`, `tests/test_leave_management_v2.py` | Admin/staff leave policy, validation, quotas and suspensions. |
| `tests/test_offline_student_sync.py` | Offline student synchronization. |
| `tests/test_pending_aggregation.py` | Pending fee aggregation behavior. |
| `tests/test_staff_list.py`, `tests_staff_list.py` | Staff list behavior. |
| `tests/test_staff_portal.py` | Staff portal authentication and views. |
| `tests/test_staff_pwa.py` | Staff PWA manifest/service worker/offline behavior. |
| `tests/test_student_bugfixes.py` | Student edge-case regressions. |
| `tests/test_teachers_management.py` | Teacher/class/subject management. |
| `tests/test_timetable.py`, `tests/test_timetable_api.py` | Timetable UI and API contracts. |
| `tests/__init__.py` | Test package marker. |

## Templates

Templates use the matching view contexts and named route contracts. Files are grouped by audience; most features have distinct desktop/mobile template files. Shared tenant components include base layouts, voucher rows/modals, fee collection fragments, and notification controls.

- `templates/tenant/`: `base.html`, `login.html`, `dashboard.html`, `student_list.html`, `student_form.html`, `student_profile.html`, `fee_collection.html`, `collect_fee.html`, `make_payment.html`, `fee_receipt.html`, `receipt.html`, `payment_history.html`, `fee_structure.html`, `fee_settings.html`, `fee_generate.html`, `family_payment.html`, `pending_fees.html`, `defaulters.html`, `reports.html`, `settings.html`, `wing_school_settings.html`, `attendence.html`, `leave_management.html`, `staff_list.html`, `staff_form.html`, `staff_profile.html`, `teachers_management.html`, `class_management.html`, `single_classes.html`, `single_class_detailed.html`, `wing_classes.html`, `wing_class_detailed.html`, `wing_school_class_management.html`, `timetable_management.html`, `timetable_periods.html`, `timetable_assignments.html`, `timetable_assign_teachers.html`, `stock_management.html`, `product_detail.html`, `sell_items.html`, `sell_separately.html`, `vouchers.html`, `voucher_modal.html`, `voucher_snippet.html`, `_voucher_row.html`, `fee_logs.html`, `global_search.html`, `messages.html`, `notification_bell.html`, `students_by_teacher.html`.
- `templates/mobile/`: mobile counterparts for dashboard, students, fees/receipts, settings, reports, stock, staff/class management and vouchers; also `more.html`, `notification_banner.html`, `notification_bell.html`, `_voucher_card.html`.
- `templates/staff/`: `base.html`, `login.html`, `dashboard.html`, `classes.html`, `class_students.html`, `student_profile.html`, `attendance.html`, `attendance_mark.html`, `profile.html`, `notifications.html`, `403.html`.
- `templates/mobile/staff/`: mobile staff dashboard/classes/student profile/attendance/leave/profile/notifications/login/biometric setup/more/base/403 templates.
- `templates/admin/password_reset_action.html`: custom Django admin action page.

The `templates/tenant/` and `templates/mobile/` trees also contain `.bak*` / `.backup*` snapshots, including alternative base, reports and timetable templates. Django template loaders target the `.html` names, not these backup suffixes.

## Static files and scripts

- Root `static/js/school_client_features.js`: school-admin feature presentation behavior.
- Root `static/js/staff_biometric.js`: browser WebAuthn client flow.
- Root `static/sw.js`: checked-in admin/root service-worker source, served dynamically by `pwa_views.py` (review both before changing behavior).
- Root `static/pwa/`: admin/staff PWA icons in PNG/SVG formats; `static/icons/` includes general app icons.
- `axis_saas/static/js/offline_student.js`: offline student form queue/sync logic.
- `axis_saas/static/pwa/`: additional admin PWA PNG icons.
- `scripts/attendance_auto_present.sh`: invokes scheduled attendance command.
- `scripts/install_attendance_cron.sh`: dry-run/install cron helper.
- `scripts/run_attendance_tests.sh`: focused attendance test runner.

`staticfiles/` is generated output from `collectstatic`, including Django admin and hashed assets; it is not hand-maintained application source. `media/` and `student_photos/` hold uploads/runtime content.
