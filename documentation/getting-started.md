# AXIS Getting Started

This is a copy-paste path for a fresh Ubuntu 24.04 development machine. It creates a local PostgreSQL database and Redis service, installs the repository dependencies, migrates the public and tenant schemas, creates a local AXIS demo tenant, and starts Django. Commands are for development only; do not reuse the local database password or settings in production.

## 1. Install system packages

Run in a terminal on Ubuntu. `sudo` may prompt for the machine user's password.

```sh
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-dev build-essential libpq-dev postgresql postgresql-contrib redis-server
sudo systemctl enable --now postgresql redis-server
```

Check both services:

```sh
sudo systemctl --no-pager --full status postgresql
sudo systemctl --no-pager --full status redis-server
```

## 2. Create a local database and role

These commands are for a fresh local PostgreSQL instance. If role/database already exist, do not re-run the `CREATE` statements; use the existing local credentials or choose a new role/database.

```sh
sudo -u postgres psql <<'SQL'
CREATE ROLE axis_dev WITH LOGIN PASSWORD 'axis_dev_local_only';
CREATE DATABASE axis_dev OWNER axis_dev;
SQL
```

This password is intentionally a local placeholder. Change it if the database is reachable by other users or networks. `axis_dev` owns its database and can create tenant schemas within it, which `django-tenants` requires.

## 3. Get the code and install Python dependencies

If the repository is not already on disk, replace `<REPOSITORY_URL>` with the team's clone URL:

```sh
git clone <REPOSITORY_URL> axis
cd axis
```

If you are already inside the checked-out AXIS repository, skip `git clone` and `cd axis`.

From the project root:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If the repository folder is named differently, the path does not matter as long as subsequent commands run from the directory containing `manage.py`.

## 4. Configure this terminal session

Export settings in the same terminal that will run migrations and the server. No root `.env` file is required.

```sh
export ENVIRONMENT=development
export DEBUG=True
export SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
export DATABASE_URL='postgresql://axis_dev:axis_dev_local_only@127.0.0.1:5432/axis_dev?sslmode=disable'
export REDIS_URL='redis://127.0.0.1:6379/1'
export ALLOWED_HOSTS='localhost,127.0.0.1'
export CSRF_TRUSTED_ORIGINS='http://localhost:8000,http://127.0.0.1:8000'
export PUBLIC_URL='http://localhost:8000'
```

The explicit `sslmode=disable` is for local PostgreSQL only; settings require SSL for normal production `DATABASE_URL` values. `PUBLIC_URL` supplies the default WebAuthn RP ID/origin. Browsers permit WebAuthn on `localhost`; remote non-HTTPS development hosts may not.

If you open a new terminal later, activate `.venv` and re-run those exports, or configure equivalent environment values in your IDE. Do not commit local secrets.

## 5. Verify settings and migrate the public schema

```sh
python manage.py check
python manage.py showmigrations
python manage.py migrate_schemas --shared
```

The first shared migration creates Django's public tables and the AXIS tenant registry. PostgreSQL must be running, and the configured role must be able to connect and create schemas.

## 6. Create a demo tenant

This creates schema `demo`, with a locally prompted administrator password. It uses the path-based portal, so a `SchoolDomain` row is not needed for local access. `SchoolClient.auto_create_schema` is enabled; the explicit tenant migration command below also ensures current tenant migrations are applied.

```sh
python manage.py shell <<'PY'
from getpass import getpass
from axis_saas.models import SchoolClient

schema_name = "demo"
if SchoolClient.objects.filter(schema_name=schema_name).exists():
    raise SystemExit(f"Tenant schema {schema_name!r} already exists; choose another name or inspect it first.")

admin_password = getpass("Set the demo school-admin password: ")
if not admin_password:
    raise SystemExit("Password cannot be empty.")

tenant = SchoolClient(
    schema_name=schema_name,
    name="AXIS Demo School",
    admin_username="admin",
    tenant_type="single_small_school",
    enabled_features=[
        "dashboard",
        "students",
        "fee_collection",
        "defaulters",
        "reports",
        "fee_structure",
        "fee_settings",
        "staff_management",
        "classes_management",
        "attendance_management",
        "timetable_management",
        "leave_management",
    ],
)
tenant.set_password(admin_password)
tenant.save()
print(f"Created AXIS tenant {schema_name!r}. Sign in as {tenant.admin_username!r}.")
PY
python manage.py migrate_schemas --tenant
```

Tenant schema creation may run schema synchronization immediately because `auto_create_schema=True`; the final command applies pending tenant migrations after creation. If schema creation/migration fails, stop and inspect PostgreSQL permissions and `showmigrations` output before retrying.

## 7. Start AXIS

```sh
python manage.py runserver 127.0.0.1:8000
```

Open the school login at:

```text
http://127.0.0.1:8000/portal/demo/login/
```

Use username `admin` and the password entered during tenant creation. The portal root is `http://127.0.0.1:8000/portal/demo/` and redirects according to the tenant's enabled features.

Stop the development server with `Ctrl+C`.

## 8. Run checks and tests

Keep PostgreSQL and Redis available. Run from the repository root with `.venv` active and the environment exports above set:

```sh
python manage.py check
python manage.py test
```

For a shorter, feature-specific pass:

```sh
python manage.py test axis_saas.tests.test_attendance_system
python manage.py test axis_saas.tests.test_timetable_api
python manage.py test axis_saas.tests.test_leave_management_v2
```

The multi-tenant test suite creates and removes schemas; use a disposable development/test database, never production.

## Re-running setup safely

- System packages and services can be checked/restarted with `systemctl`; there is no need to reinstall on every code update.
- Activate `.venv` and set environment variables again in each new terminal.
- Do not re-run public migrations blindly during a partially failed migration. Inspect `showmigrations` and database state first.
- Do not create the `demo` tenant a second time. The shell snippet deliberately stops when that schema is already registered.
- To update dependencies after pulling code, activate the environment and run `python -m pip install -r requirements.txt`, then inspect migration changes and run the appropriate migrations.
- The application does not provide a checked-in reset script or Docker Compose file. Do not drop schemas or databases as a generic troubleshooting step.

## Fresh deployment is different

This quick start is not a production deployment recipe. Production requires managed PostgreSQL and Redis, real secret values, HTTPS, a restricted `ALLOWED_HOSTS`, trusted HTTPS CSRF origins, persistent media storage, backups, and platform monitoring. Configure WebAuthn origin/RP ID to match the public HTTPS hostname.

The checked-in Docker entrypoint creates tenant `sh` with username `admin` and password `admin123` when it is missing. Do not expose that default account. Review [Operations](operations.md#deployment-behavior-in-the-docker-image) and [Security and Troubleshooting](security-and-troubleshooting.md) before using the provided image in a public environment. The repository has no `docker-compose.yml`; a real container deployment must supply reachable PostgreSQL/Redis services and tenant provisioning deliberately.
