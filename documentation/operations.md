# AXIS Development and Operations

For a clean-machine, end-to-end local setup with install, database, Redis, migration, tenant creation, and run commands, start with [Getting Started](getting-started.md).

## Requirements and local setup

Runtime dependencies are pinned in `requirements.txt`: Django 4.2.16, django-tenants 3.5.0, psycopg2-binary, dj-database-url, WhiteNoise, Gunicorn, django-environ, Pillow, WebAuthn, Redis, and django-redis. The Docker image uses Python 3.11 and installs PostgreSQL client build dependencies. PostgreSQL is mandatory for the configured schema-tenancy backend; Redis is the configured cache backend.

1. Install Python 3.11 and a PostgreSQL server with schema support; start Redis.
2. Create and activate a virtual environment, then install requirements.
3. Set the environment variables below. At minimum use a real PostgreSQL `DATABASE_URL`, a random `SECRET_KEY`, a working `REDIS_URL`, allowed hosts, and trusted HTTPS origins appropriate to your environment.
4. From project root, run `python manage.py migrate_schemas --shared`, then `python manage.py migrate_schemas` (or the hosting-specific migration workflow). The checked-in container entrypoint runs both `migrate` and `migrate_schemas --shared`; verify migration state for tenant schemas before release.
5. Create a tenant in public schema (`SchoolClient`) and set its schema, admin credentials, domain if needed, tenant type, and enabled features. `school_login` is available at `/portal/<schema_name>/login/`.
6. Run `python manage.py runserver` for local development. Production uses Gunicorn as described below.

Settings create a placeholder `DATABASES` config with database name `dummy` when `DATABASE_URL` is absent; that is not a self-contained SQLite setup and will not provide a working PostgreSQL instance. A local `DEBUG=True` fallback is selected only when no `DATABASE_URL` and no `ENVIRONMENT` are set. Set `ENVIRONMENT=production` explicitly in production.

## Environment variables

| Variable | Behavior in code |
|---|---|
| `DATABASE_URL` | PostgreSQL connection parsed by `dj-database-url`; sets django-tenants PostgreSQL backend. SSL is required unless URL includes `sslmode=disable`. |
| `SECRET_KEY` | Django secret; source has an insecure build-only fallback, which must not be used in production. |
| `DEBUG` | Explicit truthy/falsy override; ignored in favor of `False` for `ENVIRONMENT=production`. |
| `ENVIRONMENT` | `production` forces DEBUG false; `development` enables DEBUG if DEBUG not explicitly set. |
| `ALLOWED_HOSTS` | Comma-separated host list; code defaults to wildcard `*`. Set restrictive production hosts. |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated origins; adds `https://$RAILWAY_PUBLIC_DOMAIN` when set; fallback is localhost. |
| `RAILWAY_PUBLIC_DOMAIN` | Adds a Railway HTTPS origin to CSRF trusted origins. |
| `REDIS_URL` | Redis cache endpoint; defaults to local Redis DB 1. |
| `PUBLIC_URL`, `APP_URL`, `SITE_URL` | In that precedence order, choose public application URL used to derive WebAuthn RP ID and origin. |
| `WEBAUTHN_RP_ID` | Explicit WebAuthn relying-party host; defaults to `PUBLIC_URL` hostname. |
| `WEBAUTHN_ORIGIN` | Explicit WebAuthn origin; defaults to public URL without trailing slash. |
| `AI_ASSISTANT_API_KEY` | Provider API key. Set it only in the deployment secret store or an ignored local `.env`; never source control. |
| `AI_ASSISTANT_MODEL` | Model identifier for the configured OpenAI-compatible provider; required with the API key. |
| `AI_ASSISTANT_BASE_URL` | Optional OpenAI-compatible API root; defaults to `https://api.openai.com/v1`. |
| `AI_ASSISTANT_ALLOW_SCHOOL_DATA_TO_PROVIDER` | Defaults on when provider credentials exist. Set to `false` for a platform-wide hard stop. A school admin must still confirm data sharing at the start of every chat. |

To enable provider-backed data questions, add `AI_ASSISTANT_API_KEY` and `AI_ASSISTANT_MODEL` to the hosting platform's server-side secret/environment settings, then restart/redeploy the web workers. The widget enables the per-chat data-sharing choice only when credentials are present and the platform hard switch is not set to `false`. Never put an API key in chat, browser JavaScript, templates, documentation, or version control. Settings also reads a root `.env` locally if present; no `.env` file is checked in.

The assistant API remains disabled until **AI Assistant** is selected under that school's **Desktop Features**. Every time a school admin opens a new chat, the widget asks them to choose private mode or explicitly allow provider processing for that chat. The server binds approval to a fresh conversation ID, scopes history to that conversation, and revokes approval/history when the chat ends. Without per-chat approval or while the platform hard switch is off, the model receives no school-data tools. The allow-listed query tool supports count, filter, group, sum, average, and small-list operations across 38 reviewed tenant-local datasets spanning student/staff records, fees/payments, attendance/audit/policy, leave/policy, inventory/sales, class/subject, timetable/calendar, and school configuration. Public tenant/domain identity and staff credential models are excluded; guardian contact/CNIC, addresses, staff credentials, freeform notes/reasons, and arbitrary JSON blobs are not exposed. Every dataset rechecks its module feature and executes inside the URL tenant's schema. High-volume datasets require inclusive date bounds capped at 366 days, and list results are capped at 25 rows. Specialized tools handle common student/parent lookups and fee/attendance summaries locally. Fee collection is period-based while outstanding balance is a current snapshot. Documentation retrieval and enabled-page navigation are also available. Chat write actions are not available.

Requests are limited to 30 per authenticated school-admin session per minute, keyed by tenant schema and session in Django's configured cache. Cache errors fail closed and emit a warning; use the shared Redis cache in production, not a per-process local cache. Provider calls have an 18-second timeout. Missing credentials return `provider_status: unconfigured`; an upstream or malformed-response failure returns HTTP 503 with `provider_status: unavailable`; a successful turn returns `provider_status: ready`. Monitor application warning logs and provider-side usage/error dashboards; never log API keys, full prompts, or tool results.

## Common commands

### Current AI data access

Aggregate/count/group queries can cover all-time records or a requested longer period. High-volume list queries remain capped to inclusive 366-day ranges, but return `next_offset` so users can page through matching records.

Knowledge retrieval now searches the Markdown help center and visible copy/accessibility labels from tenant admin templates. It strips Django substitutions, scripts, and styles before indexing; live values still come from authorized database tools.

This is the current contract and supersedes earlier assistant field-scope wording above: after the admin confirms data mode for a chat, the generic query tool can read all concrete database fields on the 38 tenant-local operational models, including contact details, notes, reasons, and JSON values. It still excludes the four public/authentication models (`SchoolClient`, `SchoolDomain`, `StaffCredential`, and `StaffBiometricCredential`) and file contents. Queries run only in the URL-selected tenant schema, recheck each module feature, and cannot write. Date scans remain bounded and list operations return at most 25 rows per call.

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py check
python manage.py showmigrations
python manage.py migrate_schemas --shared
python manage.py migrate_schemas
python manage.py test
```

Django tenant migration commands depend on the django-tenants package and connected database. Confirm the exact supported command/options against the installed version before running operational migrations. Avoid using direct schema/table creation repairs as a substitute for fixing migration history.

Focused tests can be invoked by test module, for example:

```sh
python manage.py test axis_saas.tests.test_attendance_system
python manage.py test axis_saas.tests.test_timetable_api
python manage.py test axis_saas.tests.test_leave_management_v2
python manage.py test axis_saas.tests.test_ai_assistant
```

The helper `scripts/run_attendance_tests.sh` accepts `--quick`, `--auto-mark`, `--dashboard`, or `all`. These tests use tenant schemas and may require a PostgreSQL role with permission to create/drop schemas; run them against a disposable test database, never production.

## Deployment behavior in the Docker image

`Dockerfile` builds from `python:3.11-slim`, installs requirements, copies the entire project, creates `/data/staticfiles` and `/data/media`, injects a dummy `DATABASE_URL` for build-time static collection, runs `collectstatic`, exposes port 7860, and starts `/start.sh`.

`start.sh` waits up to 30 seconds for PostgreSQL, runs `migrate` and `migrate_schemas --shared`, then creates a default tenant with schema `sh` and credentials `admin` / `admin123` if absent, and starts Gunicorn on `0.0.0.0:7860` with 2 workers, 4 threads, and `gthread`. This default account is a serious deployment hazard: replace/disable it or change its credentials before any public deployment, and verify the tenant's schema/domain/features and migrations. The script does not show a Redis readiness check. The paths `/data/staticfiles` and `/data/media` are created, but settings set `STATIC_ROOT` to project-root `staticfiles` and `MEDIA_ROOT` to project-root `media`; verify mounted volumes and platform persistence rather than assuming those `/data` folders are used.

`SECURE_PROXY_SSL_HEADER` trusts `HTTP_X_FORWARDED_PROTO`; deploy only behind a proxy that sets that header correctly. TLS, host restrictions, database backups, media durability, Redis availability, log aggregation, and worker health checks are platform responsibilities not defined by this repository.

## Management commands

All commands below are in `axis_saas/management/commands/`. Read the command source and `--help` before production use; several are repair/data mutation tools.

| Command | Purpose / caution |
|---|---|
| `add_staff_feature_to_tenants` | Adds the staff-management feature for existing tenants. |
| `apply_late_fees` | Applies late fees to overdue fee records. |
| `attendance_auto_absent` | Marks unmarked students absent according to policy. |
| `attendance_auto_present` | Automatically fills attendance; supports date/schema and mode options. Used by attendance cron helper. |
| `attendance_monthly_report` | Exports previous-month attendance as CSV per tenant. |
| `attendance_reminder` | Notifies class teachers with unmarked class attendance. |
| `auto_generate_fees` | Generates monthly fees where tenant automation is enabled. |
| `generate_monthly_fees` | Generates monthly fee records for tenants based on configured generation day. |
| `backfill_custom_fee` | Backfills student custom fees from grade fee structures. |
| `backfill_fee_structures` | Backfills custom fees and can create missing fee structures with configurable defaults. |
| `backfill_student_fees` | Backfills student custom fees across tenants. |
| `backfill_dayschedule_updated_at` | Fills legacy DaySchedule version timestamps. |
| `check_cron` | Reports fee automation cron status. |
| `check_payments` | Checks payment integrity and runs a test query. |
| `check_schema_columns` | Checks expected tenant schema columns; supports schema selection. |
| `check_student_fees` | Checks student fee records/payments. |
| `create_test_notification` | Creates a test notification for a required tenant schema. |
| `enable_leave_feature` | Enables leave feature; supports schema/all/dry-run options. |
| `expire_leave_suspensions` | Expires dated staff leave suspensions; can target a schema. |
| `fix_dayschedule_columns` | Repairs missing DaySchedule columns. Schema-changing; use only after inspecting its implementation. |
| `fix_fee_data` | Repairs student grade/FeeStructure consistency; has dry-run and schema options. |
| `fix_missing_tables` | Attempts to create missing tables by running migrations across tenant schemas. |
| `fix_orphan_payments` | Checks orphaned payments; supports deletion option. |
| `fix_orphaned_payments` | Deletes or reassigns orphaned payments; destructive options. |
| `fix_timetable_tables` | Generates migrations/creates missing timetable tables; inspect before running. |
| `hash_existing_passwords` | Hashes plaintext `SchoolClient` admin passwords. |
| `inspect_tenant_schema` | Prints tables/columns for a named tenant. |
| `list_classes` | Lists classes, subjects, and assignments for a tenant. |
| `list_notifications` | Lists a tenant's notifications; can include read items. |
| `normalize_class_data` | Normalizes stored class/subject names. |
| `recalc_fee_paid_amounts` | Recomputes FeeRecord paid totals from payments; supports schema and dry-run. |
| `repair_student_fees` | Generates missing monthly fee records; supports month/year/force. |
| `sync_all_schemas` | Synchronizes all tenant schemas, creating missing tables/columns. High-impact; inspect before use. |

Some commands overlap in purpose or represent historical repairs. Do not run a repair command just because a similarly named issue appears; first take a backup, inspect its target schema and behavior, and prefer a dry run where available.

## Scheduled attendance work

`scripts/attendance_auto_present.sh` invokes the attendance auto-present management command. `scripts/install_attendance_cron.sh` prints a daily 03:05 local-time crontab line by default; `--install` edits the current user's crontab and `--time` overrides the schedule. The helper is idempotent by marker, writes logs under a `logs/` path, and depends on executable script/cron availability. It is not automatically installed by Docker startup. Attendance also has a lazy catch-up helper (`trigger_lazy_auto_mark`) with a seven-day window and one-hour per-tenant Redis lock; cron and lazy recovery have different scheduling guarantees.

## Tests and regression coverage

The checked-in tests focus heavily on attendance, dashboard aggregates, staff portal/PWA, leave, teacher assignment, timetable, offline student sync, and fee calculations. See full names in [Code Map](code-map.md). For multi-tenant changes, include a test that proves cross-schema isolation, not just a single-tenant happy path.

No test suite was run while writing these docs. Run `python manage.py check` and focused tests after code changes in an environment with dependencies, PostgreSQL, and Redis configured.

## Troubleshooting

| Symptom | Checks |
|---|---|
| Tenant URL says not found or uses public data | Confirm `/portal/<schema>/...`, a `SchoolClient` row in public schema, schema existence/migrations, and that path middleware runs before views. |
| Tenant login redirects repeatedly | Inspect session keys, `school_admin_schema` equality, public-schema session table, cookie settings, and tenant URL spelling. |
| Staff portal redirects to login | Check staff session identity and cached `staff_session_token:<schema>:<id>`; verify Redis reachability, `StaffCredential` public record, active tenant staff row, and session schema. |
| Staff device always redirected to biometric setup | Verify per-staff `biometric_login_enabled`, public `StaffBiometricCredential`, public URL/RP ID/origin and HTTPS requirements. |
| Cache appears stale | Confirm Redis and schema-prefixed cache invalidation signals; identify direct `QuerySet.update()` calls, which bypass model save signals. |
| Attendance rows are missing | Check tenant AttendancePolicy, holiday tables, command/lazy trigger, class/student active flags, date timezone, and unique full-day/period constraints. |
| Timetable teacher grid has stale slots | Inspect DaySchedule changes, signal/on-commit reconciliation logs, assigned timetable day JSON, and `PeriodTeacherAssignment`; do not delete rows manually without checking historical intent. |
| Static asset manifest errors | Run `collectstatic`; confirm static root and WhiteNoise storage; ensure referenced source files exist before hashed-manifest lookup. |
| AI assistant reports provider unavailable | Check provider credentials/model/base URL, outbound HTTPS, provider status/usage, and the 18-second request timeout. `provider_status: unconfigured` means credentials/model are absent; `unavailable` means the configured call failed. |
| AI assistant asks to retry while provider is healthy | Check Redis/cache health and the `AI assistant rate-limit cache failed` warning. The endpoint fails closed when it cannot enforce request limits. |
| Django admin/root works but portal fails | Root public URL config may work while tenant path/schema lookup, public records, tenant migration, or custom session state is wrong. |
| Container starts without Redis | Current entrypoint waits for PostgreSQL only; verify Redis separately because session token/cache features depend on it. |
