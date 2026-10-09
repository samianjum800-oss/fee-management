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

The migration package contains the following numbered files; read their dependencies and operations before editing schema history.

| Migration file | Change area (from filename and migration history) |
|---|---|
| `0001_initial.py` | Initial AXIS schema. |
| `0002_repair_missing_schema.py` | Repair initial missing schema state. |
| `0003_staffbiometriccredential.py` | Staff biometric credential registry model. |
| `0004_alter_schoolclient_tenant_type.py` | Tenant type field/choice evolution. |
| `0005_alter_schoolclient_tenant_type.py` | Follow-up tenant type migration. |
| `0006_alter_schoolclient_tenant_type.py` | Follow-up tenant type migration. |
| `0007_wingcategory_alter_schoolclass_unique_together_and_more.py` | Wing hierarchy and class uniqueness changes. |
| `0008_drop_staff_father_name.py` | Remove legacy staff field. |
| `0009_academiccalendar_holiday_period_timetableentry.py` | Calendar, holiday, period and timetable-entry models. |
| `0010_dayschedule.py` | Day schedule model. |
| `0011_alter_dayschedule_add_order_label.py` | Day-schedule ordering and label fields. |
| `0012_alter_dayschedule_label_not_null.py` | Make day-schedule label required. |
| `0013_vacation_weeklyholiday_alter_dayschedule_options_and_more.py` | Vacation/weekly holiday and schedule options. |
| `0014_add_break_fields_to_dayschedule.py` | Schedule break fields. |
| `0015_schedulelabel.py` | Reusable schedule label model. |
| `0016_dayschedule_unique_label_per_day.py` | Unique label/calendar/day schedule rule. |
| `0017_periods_timetable.py` | Persisted periods timetable. |
| `0018_period_teacher_assignment.py` | Per-period teacher assignments. |
| `0019_dayschedule_ci_label_unique.py` | Case-insensitive schedule label uniqueness. |
| `0020_dayschedule_optimistic_lock.py` | Day-schedule concurrency/version field. |
| `0021_schedulelabel_fk_step1.py` | Schedule label foreign-key conversion step 1. |
| `0022_schedulelabel_fk_step2.py` | Schedule label foreign-key conversion step 2. |
| `0023_schedulelabel_fk_step3.py` | Schedule label foreign-key conversion step 3. |
| `0024_leave_management.py` | Staff leave management models. |
| `0025_rename_axis_saas_l_staff_i_2e5d1b_idx_axis_saas_l_staff_i_b29c3c_idx_and_more.py` | Index name changes. |
| `0026_leave_suspensions.py` | Staff leave suspension model. |
| `0027_substitute_assignment.py` | Substitute/fixture assignment model. |
| `0028_staff_biometric_login_enabled.py` | Per-staff biometric login switch. |
| `0029_rename_axis_saas_l_staff_i_act_idx_axis_saas_l_staff_i_7f7c6d_idx.py` | Leave index rename. |
| `0030_leave_hardening_v3.py` | Leave policy hardening. |
| `0031_period_teacher_assignment_audit.py` | Assignment audit fields. |
| `0032_attendance_production_v2.py` | Production attendance schema. |
| `0033_attendance_auto_system_source.py` | Automatic attendance source option. |
| `0034_class_teacher_attendance_permissions.py` | Class-teacher permissions and edit quota. |
| `0035_rename_axis_saas_attaudit_ca_idx_axis_saas_a_changed_c271c5_idx_and_more.py` | Attendance audit index rename. |
| `0036_class_timetable_assignment_multi.py` | Multiple timetable assignments per class. |

`migrations/__init__.py` is the package marker. Descriptions are signposts only; migration operations are authoritative.

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

Templates use view contexts and named URL contracts. The following are the active `.html` template paths in the tracked tree; files with backup suffixes are listed separately and are not selected by the normal template names.

- `templates/tenant/`: `_voucher_row.html`, `attendence.html`, `base.html`, `class_management.html`, `collect_fee.html`, `dashboard.html`, `defaulters.html`, `family_payment.html`, `fee_collection.html`, `fee_generate.html`, `fee_logs.html`, `fee_receipt.html`, `fee_settings.html`, `fee_structure.html`, `global_search.html`, `leave_management.html`, `login.html`, `make_payment.html`, `messages.html`, `notification_bell.html`, `payment_history.html`, `pending_fees.html`, `product_detail.html`, `receipt.html`, `reports.html`, `sell_items.html`, `sell_separately.html`, `settings.html`, `single_class_detailed.html`, `single_classes.html`, `staff_form.html`, `staff_list.html`, `staff_profile.html`, `stock_management.html`, `student_form.html`, `student_list.html`, `student_profile.html`, `students_by_teacher.html`, `teachers_management.html`, `timetable_assign_teachers.html`, `timetable_assignments.html`, `timetable_management.html`, `timetable_periods.html`, `voucher_modal.html`, `voucher_snippet.html`, `vouchers.html`, `wing_class_detailed.html`, `wing_classes.html`, `wing_school_class_management.html`, `wing_school_settings.html`, `wing_school_student_form.html`.
- `templates/mobile/`: `_voucher_card.html`, `base.html`, `class_management.html`, `collect_fee.html`, `dashboard.html`, `defaulters.html`, `fee_collection.html`, `fee_logs.html`, `fee_settings.html`, `fee_structure.html`, `more.html`, `notification_banner.html`, `notification_bell.html`, `product_detail.html`, `receipt.html`, `reports.html`, `sell_separately.html`, `settings.html`, `staff_form.html`, `staff_list.html`, `staff_profile.html`, `stock_management.html`, `student_form.html`, `student_list.html`, `student_profile.html`, `vouchers.html`, `wing_school_class_management.html`, `wing_school_settings.html`, `wing_school_student_form.html`.
- `templates/staff/`: `403.html`, `attendance.html`, `attendance_mark.html`, `base.html`, `class_students.html`, `classes.html`, `dashboard.html`, `login.html`, `notifications.html`, `profile.html`, `student_profile.html`.
- `templates/mobile/staff/`: `403.html`, `attendence.html`, `base.html`, `biometric_setup.html`, `classes.html`, `dashboard.html`, `leave_management.html`, `login.html`, `more.html`, `notifications.html`, `profile.html`, `student_profile.html`.
- `templates/admin/`: `password_reset_action.html`.

Tracked tenant template backups: `templates/tenant/base.html.backup_final`, `base.html.backup_final2`, `base.html.backup_professional`, `base.html.bak`, `base.html.bak_final`, `base.html.bak_final_ui`, `base.html.bak_scroll`, `base.html.bak_ui`, `reports.html.bak_reports`, `timetable_management.html.bak`, `timetable_management.html.bak2`, `timetable_management.html.bak3`, `timetable_management.html.bak_dupmsg`, `timetable_management.html.bak_final`, `timetable_management.html.bak_labels`, `timetable_management.html.bak_v2`. Django template loaders target the active `.html` names, not these backup suffixes.

## Static files and scripts

- Root `static/`: `icons/icon-192x192.png`, `icons/icon-512x512.png`, `js/school_client_features.js`, `js/staff_biometric.js`, `pwa/icon-192x192.png`, `pwa/icon-512x512.png`, `pwa/staff-icon-180.png`, `pwa/staff-icon-192.png`, `pwa/staff-icon-192.svg`, `pwa/staff-icon-512.png`, `pwa/staff-icon-512.svg`, `sw.js`. `static/sw.js` is checked-in admin/root service-worker source served dynamically by `pwa_views.py`; review both before changing behavior.
- `axis_saas/static/`: `js/offline_student.js`, `pwa/icon-192x192.png`, `pwa/icon-512x512.png`.
- `scripts/`: `attendance_auto_present.sh` (scheduled attendance command), `install_attendance_cron.sh` (cron dry-run/install helper), `run_attendance_tests.sh` (focused attendance test runner).

`staticfiles/` is generated output from `collectstatic`, including Django admin and hashed assets; it is not hand-maintained application source. `media/` and `student_photos/` hold uploads/runtime content.
