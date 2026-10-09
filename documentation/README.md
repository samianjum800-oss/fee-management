# AXIS Developer Documentation

This folder is the developer handbook for the AXIS Django multi-tenant school management system. It describes the checked-in application as implemented; where deployment scripts or legacy files create operational risks, those are called out explicitly.

## Find your way

| I need to... | Read |
| Set up AXIS on a fresh Ubuntu machine with terminal commands | [Getting Started](getting-started.md) |
|---|---|
| Understand runtime structure, tenant isolation, authentication, or request flow | [Architecture](architecture.md) |
| Understand school/staff features and their major workflows | [Features](features.md) |
| Find a URL, endpoint name, auth wrapper, or owning view | [API and Routes](api.md) |
| Understand database entities and relationships | [Data Model](data-model.md) |
| Set up, test, deploy, troubleshoot, or run a management command | [Operations](operations.md) |
| Locate a module, template, migration, test, script, or legacy file | [Code Map](code-map.md) |

## Project at a glance

- Django 4.2 application package: `axis_saas`.
- PostgreSQL with `django-tenants`; tenant selection is path-based at `/portal/<schema_name>/`, not hostname-based.
- School-admin portal, separate staff portal, Django admin, and progressive web app surfaces.
- Major domains: student records, fees and receipts, stock/sales, staff, classes/subjects, timetables, student/staff attendance, leave, notifications, vouchers, and reports.
- UI is server-rendered Django templates with separate tenant, mobile, and staff template families; browser behavior is in static JavaScript and served service workers.

## Source-of-truth notes

The active root URL configuration is `axis_saas.public_urls`, as selected by `ROOT_URLCONF` in settings. It imports views from the `axis_saas.views` package. `axis_saas/urls.py`, `.bak*` / `.backup*` files, and `axis_saas/views_fix.py` are not the active route tree. `axis_saas/tenant_urls.py` is configured as `TENANT_URLCONF` but the custom middleware routes `/portal/` through the root URL configuration; it is not the main set of portal routes.

This handbook intentionally distinguishes source code from generated `staticfiles/`, user uploads (`media/`, `student_photos/`), and database snapshots. Those artifacts are not the Django implementation surface. The file map covers the checked-in application and its developer-facing assets/scripts.

## Fast path for a new developer

1. Read [Architecture](architecture.md), especially the schema-routing and authentication sections.
2. Follow a feature from [Features](features.md) to its route in [API and Routes](api.md), then to its owning view/model in [Code Map](code-map.md) and [Data Model](data-model.md).
3. Follow [Getting Started](getting-started.md) for a copy-paste Ubuntu setup; use [Operations](operations.md) for environment details and deployment behavior.
4. Run focused tests before changing tenant-aware behavior. Review the test suite list in [Code Map](code-map.md).

## Accuracy boundary

The repository does not include a complete API schema/OpenAPI contract or a formal permission matrix. Endpoint paths and their wrappers are documented from URL configuration; payload details remain in the view implementation. Production platform secrets, tenant data, configured cron jobs, and live infrastructure cannot be inferred from source alone.
