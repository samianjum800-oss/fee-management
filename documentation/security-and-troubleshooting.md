# AXIS Security and Troubleshooting Notes

This page records behavior visible in the source and points to the owner modules. It is not a replacement for a production threat model or deployment review.

## Security checks for developers

- **Tenant authorization:** A schema name in the URL is an identifier, not authorization. Keep `portal_wrapper` and the school-admin schema-bound session check on tenant admin routes. For cross-schema reads/writes, use explicit `schema_context()` and verify the intended tenant.
- **Root APIs:** `debug_payments_api`, `fee_status_api`, `manual_generate_api`, and `manual_generate_single_api` are registered at public root paths without the tenant-admin wrapper in URLconf. Inspect implementation and deployment exposure before using them in production.
- **Known admin default:** `start.sh` creates tenant `sh` using `admin` / `admin123` if absent. Disable or rotate before exposure; do not assume tenant provisioning secrets are secure merely because `SchoolClient` hashes passwords later.
- **Debug / host settings:** Settings contain a build-only secret fallback and default `ALLOWED_HOSTS=['*']`; use a strong `SECRET_KEY`, `ENVIRONMENT=production`, explicit host list, correct CSRF origins and TLS proxy headers.
- **Staff sessions:** Staff route protection depends on session fields plus a Redis token. Treat Redis availability as authentication-sensitive. Ensure login, logout, forced logout, and admin status changes preserve token invalidation.
- **Credential data:** Staff credentials may carry `visible_password` for account provisioning/display. Avoid adding logs, broad serialization, or client caching that could expose it. Public-schema identity rows are cross-tenant sensitive.
- **WebAuthn:** RP ID and origin must match the browser-visible HTTPS origin. Test passkey registration/login with the production hostname and reverse proxy configuration.
- **CSRF:** Browser POST routes should remain CSRF protected. Decorators need `functools.wraps` so Django sees underlying view attributes. Do not blanket-exempt API views.
- **PWA caches:** Staff service worker must not cache authenticated portal/API responses. Main PWA worker explicitly excludes staff URLs and student mutation paths. Test logout/login with two staff accounts on one device after worker changes.
- **Model signals:** Signals perform cache invalidation and attendance/timetable writes. Use ORM-aware tests and schema-aware callbacks; bulk operations bypass ordinary `post_save`/`post_delete` signals.
- **Data repair scripts:** `back.py` can perform hard git reset; `push.py` stages and pushes every change; `g.py` can rewrite source. These are not application commands; do not run them without understanding their effects.

## Tenant isolation test checklist

1. Create two tenants with overlapping local IDs and different records.
2. Authenticate to tenant A and attempt every read/write path using tenant B's schema slug.
3. Verify wrappers bind the session to one schema and staff tokens bind both staff ID and schema.
4. Exercise public-schema lookups and cleanup paths explicitly.
5. Confirm cache keys include tenant schema where data is tenant-scoped.
6. Test public, tenant-admin, staff and Django admin surfaces separately.

## Frequent operational failure modes

### `No tenant for hostname` or wrong tenant selected

Current tenant resolution is URL-path based. Verify the request begins with `/portal/<schema_name>/`, `SchoolClient.schema_name` exists in public schema, and the schema has completed migrations. A `SchoolDomain` record is not consulted by `URLPathTenantMiddleware` for current routing.

### Tenant session works on one page but not another

Check the custom session backend persists Django sessions in `public`, that cookies use `/`, and that school session schema matches the current route. Look for routes missing the standard wrapper or a view that changes connection schema and fails to restore it.

### Staff portal loops to login or setup

Check Redis token `staff_session_token:<schema>:<staff_id>`, session `staff_session_token`, `staff_id`, `staff_schema_name`, and cached logout state. Then check active staff record and biometric credential/feature switch. Login, manifest, service worker, offline and biometric endpoints are explicitly allowlisted by the staff middleware; other pages require a staff identity.

### Database migrations appear successful but tenant tables are absent

Use `showmigrations`, inspect public and tenant schemas, and confirm `axis_saas` migration state in django-tenants. `fix_missing_tables`, `fix_timetable_tables`, `fix_dayschedule_columns`, and `sync_all_schemas` are repairs, not safe substitutes for understood migration history. Back up first.

### Incorrect fees or stale payment balances

Review `FeeRecord.save()` status calculations, payment-to-record M2M links, fee extras/late accrual, and any queryset-level bulk updates that bypass save logic. Use `recalc_fee_paid_amounts` only after a dry-run/backup; `FeeStructure.save()` pushes the new grade fee to every matching student.

### Student class/wing label crashes or looks flat

`utils/class_display.py` and `utils/display_grade.py` defensively fall back when wing references are missing. Check `SchoolClass.wing_category`, category parent relations and tenant type. Class display can intentionally be flat for single-school tenants.

### Attendance records missing, duplicated, or unexpectedly auto-marked

Review attendance policy, date timezone (`Asia/Karachi`), weekly/annual holidays and vacations, approved StudentLeave, uniqueness constraints, class/student active flags, cron timing and the lazy-mark Redis key. Full-day rows use `period_order=NULL`; period rows use an integer slot. Signal-created rows may use `auto_leave` or `auto_system` source.

### Schedule changes leave stale teacher assignments

`DaySchedule` save/delete schedules an after-commit reconciliation. Check logs, active schema, day schedule period counts and `PeriodTeacherAssignment`; save operations should go through the current views and not direct SQL. Teacher assignment reconcile removes orphan slots after period reductions.

### Assets fail only in production

The project uses WhiteNoise and `CompressedManifestStaticFilesStorage`. Run `collectstatic`, ensure every referenced file exists, and verify deployed `STATIC_ROOT`. The Dockerfile creates `/data/staticfiles`, while settings point to `BASE_DIR/staticfiles`; confirm the hosting volume configuration.

## Debugging sequence

1. Identify the exact URL name/path and route source in `public_urls.py` or `staff_urls.py`.
2. Confirm the resolved view module and wrapper/decorator chain.
3. Log schema name and object IDs (never passwords/tokens/credential private material).
4. Inspect relevant model constraints/signals and tenant context.
5. Reproduce in a focused tenant-aware test from the related test module.
6. Check PostgreSQL migration state and Redis cache/token state.
7. Use repair commands only after reading their source and backing up data.
