# AXIS Features

This is the functional map of the school-admin and staff-facing product surfaces visible in the current code. Endpoint paths and names are listed in [API and Routes](api.md); the underlying records are in [Data Model](data-model.md).

## Tenant configuration and feature flags

`SchoolClient` contains a `tenant_type` (`wing_school` or `single_small_school`; legacy `school` is accepted by feature helpers), `enabled_features`, and school-admin credentials. Feature data accepts either a legacy list or a dictionary grouped by channel. `is_feature_enabled(key, channel)` handles both. The school feature key choices are:

`class_management`, `classes_management`, `dashboard`, `students`, `fee_collection`, `defaulters`, `reports`, `stock_management`, `fee_structure`, `fee_settings`, `family_payment`, `staff_management`, `timetable_management`, `leave_management`, `attendance_management`.

Staff portal keys: `staff_dashboard`, `staff_classes`, `staff_attendance`, `staff_profile`, `staff_notifications`, `staff_more`, `staff_leave_management`. Channel names include `desktop`, `mobile`, and `staff_portal`. The context processor computes staff portal feature visibility for templates. Feature hiding/visibility is not a substitute for server-side authorization: routes still require their configured session wrapper, and every new feature should enforce access at the view/API boundary.

## School administration

### Dashboard, search, and notifications

The dashboard aggregates school-facing activity and includes attendance/staff data. Search APIs provide tenant-wide global search and dedicated student/staff search. Dashboard and common aggregate caches are invalidated by model signals. Notifications are listed, dismissed, marked read individually, and marked all read; tenant `Notification` rows are ordered newest first.

### Student records and offline entry

School admins can list, add, edit, and view students, with desktop/mobile templates and profiles. Student data includes contact/guardian identifiers, grade and section, class and optional wing/campus, status, photos, notes, custom fee, default extra charges, and an automation toggle. Student save logic derives grade/section from the selected class, fills a grade-based default custom fee on creation only, and allocates a unique roll number with transaction/unique-conflict retries.

Mobile/offline student creation is supported by `offline_student.js` and `sync_offline_student_api`. Review that API and the offline client together when changing identifiers, duplicate detection, or validation; the cache worker deliberately avoids caching student-list/create/edit routes.

### Fees, collection, receipts, and vouchers

The fee domain has grade-level `FeeStructure`, per-student monthly `FeeRecord`, tenant-level `SchoolFeeSettings`, payment transactions, receipt numbers, extra charges, late-fee accrual, and generation logs. Admin workflows include:

- Generate one or multiple months of fee records, manually or by automation.
- Collect a payment against one or more fee records, including family payment keyed by guardian CNIC.
- Produce/view receipts and inspect student payment/fee-record histories.
- Configure generation date, due-date offset, percentage late penalty, and default extra charges.
- View pending fees, defaulters, reports, fee logs, voucher status, and generated voucher HTML.

`FeeRecord.save()` derives status from remaining total (including extras and accrued late fees), paid amount, and due date. A payment is linked to fee records through a many-to-many field; receipt numbers are generated using a date prefix and count. The management command `recalc_fee_paid_amounts` exists for repairing denormalized paid totals. Verify transaction atomicity and allocation rules before changing payment workflows.

### Stock and sales

Product categories and products provide tenant-local stock inventory, SKU, quantity, and selling price. Admin views support desktop/mobile stock lists, product detail, category/product creation/removal, and separate product sale workflows. Sales can be attached to a payment as `SaleItem` lines. There are product-list APIs and mobile views; see route catalog.

### Staff administration

School admins can create, list, search, edit, view, enable/disable, force logout, reset credentials, and toggle biometric login for tenant staff. Staff roles include teacher, class teacher, subject teacher, and admin; flags govern attendance/fee capabilities, and class/subject assignments connect staff to teaching responsibilities. Staff credentials are created/maintained in the public-schema registry. Password reset and credential display behavior should be treated as sensitive; do not expose credentials in logs or new APIs.

### Classes, wings, subjects, and assignments

`wing_school` tenants can create hierarchical campus/wing categories; classes link to an optional wing and enforce uniqueness within that category by name and section. `single_small_school` tenants use flat class names. Student and class forms switch fields based on tenant type. Class names are normalized (title-case class name, uppercase section), and duplicate checks are case-insensitive.

The product supports class and subject CRUD, mapping a subject to a class with an assigned teacher and academic year, class-teacher assignment, staff assignment views, class rosters and detail pages. The `/classes/` admin route redirects to the `/teachers/` management area; `/my-classes/` pages provide the class cards/detail surface. Wing-specific and single-school view/template pairs format class labels differently.

### Timetable and substitute planning

Timetable setup includes an academic calendar, working days/times, periods, school holidays, weekly holidays, annual holidays, vacations, reusable schedule labels, and multiple saved `PeriodsTimetable` records. Timetables may be assigned to a class; multiple timetables per class are supported subject to a same-label rule enforced in the assignment view. Period teacher assignments map class/day/period slots to subject/teacher, and substitute assignments create date-specific coverage without mutating the base assignment.

Timetable APIs support calendar/day-schedule edits, period and break controls, holiday CRUD, schedule-label CRUD/batch time changes, timetable retrieval/save, class assignment/unassignment, teacher assignment retrieval/save, leave lookup, and substitute operations. `DaySchedule` writes trigger after-commit reconciliation; old and orphaned teacher slots can be removed when the available periods change. Optimistic version checks are used on schedule editing paths; inspect `views/timetable.py` and `views/periods.py` before modifying their payload contracts.

### Attendance: students and staff

The attendance system supports daily/full-day and period-wise student marking; present, absent, late, half-day, excused, and holiday states; teacher/admin/system sources; date/class/student queries; bulk updates; summaries, compliance, low-attendance defaulters, and audit history. `AttendancePolicy` controls mode, lateness threshold, low-attendance threshold, automatic absent time, notifications, teacher backdating, and approval policy.

Class-teacher permissions specify past-date access, history/edit windows, and maximum edits per class/date. `ClassTeacherEditQuota` tracks teacher edits separately from admin changes. Staff attendance is a daily check-in/check-out record with late/worked-minute fields and sources including biometric, manual/admin, leave, and holiday automation.

Approved student leave auto-upserts full-day `excused` attendance and writes an audit log. Approved staff `LeaveRequest` dates are synchronized to `StaffAttendance(status='on_leave')`. A lazy attendance catch-up helper can fill up to seven past days once an hour per tenant using Redis; a cron command also supports scheduled auto-marking. See [Operations](operations.md) for scheduling cautions.

### Staff portal and biometric sign-in

The staff portal is independent from the school-admin session. Staff members access dashboard, class/roster and student profile views, notifications, profile/password, attendance, and leave application/history. Staff feature flags are evaluated separately. Staff views use the current staff session to scope access, including class-teacher and subject-teacher assignment rules.

WebAuthn supports credential status, registration options, credential registration/disable, and challenge preparation/completion. Registration identity is bound to a staff ID and tenant schema in the public registry. The administrator can switch biometric login off per staff profile. RP ID and origin are derived from `PUBLIC_URL`/`APP_URL`/`SITE_URL`, or can be explicitly set.

The staff portal has its own installable PWA manifest, service worker, icons, and cached offline fallback. It intentionally does not cache authenticated pages or API responses. The main/admin PWA has a separate service worker and tenant-aware manifest.

### Staff leave and suspension controls

Staff can submit leave requests, inspect their leave history and policy, and cancel eligible requests. Admins can inspect request detail, approve/reject, configure a tenant-wide singleton policy, view staff summaries, and suspend/unsuspend staff from submitting leave. Policy includes monthly/weekly/consecutive-day limits, backdating, working-day-only counting, pending-vs-approved counting, rejection threshold, and suspension duration. Stale suspensions can be expired by a command. The leave implementation includes quota validation, working-day cache invalidation, and conflict-safe mutation logic; consult both admin and staff leave views.

## Feature state and implementation boundaries

The feature-choice constants describe available flags, but route configuration does not uniformly apply feature-flag gates. Several views evaluate feature state, and context processors may hide navigation, but the authentication wrappers are explicit in `public_urls.py` / `staff_urls.py`. When adding a gated module, confirm both navigation and server-side route enforcement for each role. Do not infer that an absent menu item makes a URL inaccessible.
