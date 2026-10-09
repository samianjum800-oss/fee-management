# AXIS API and Routes

All paths below are registered by `axis_saas.public_urls` or `axis_saas.staff_urls`. `<schema_name>` is a tenant schema slug. Most tenant routes are wrapped with `portal_wrapper(login_required_for_schema(...))`; staff routes live under `/portal/staff/` and use staff session middleware/decorators. The endpoint code determines allowed methods, JSON shape, and validation. This repository does not declare an OpenAPI schema.

## Public and utility routes

| Path | Name / view | Access boundary |
|---|---|---|
| `/` | `saas_homepage` | Public HTML response. |
| `/admin/` | Django admin | Django admin authentication/permissions. |
| `/api/debug-payments/` | `debug_payments_api` | Not wrapped by tenant-admin login in URLconf; inspect view before exposure. |
| `/api/fee-status/` | `fee_status_api` | Not wrapped by tenant-admin login in URLconf; inspect view before exposure. |
| `/api/manual-generate/` | `manual_generate_api` | Not wrapped by tenant-admin login in URLconf; inspect view before exposure. |
| `/api/manual-generate-single/` | `manual_generate_single_api` | Not wrapped by tenant-admin login in URLconf; inspect view before exposure. |
| `/sw.js` | `service_worker` | Public admin/root PWA service worker. |

The file `axis_saas/urls.py` separately declares `/admin/` and `/voucher/html/<student_id>/`, but settings do not select it. The registered tenant voucher HTML API is instead `/portal/<schema_name>/api/student/<student_id>/voucher-html/`.

## Tenant-admin UI routes

| Path | Name | Purpose |
|---|---|---|
| `/portal/<schema_name>/` | `tenant_root` | Redirect to the first configured/enabled default feature. |
| `/portal/<schema_name>/login/` | `school_login`, alias `tenant_login` | School-admin login. |
| `/portal/<schema_name>/logout/` | `school_logout`, alias `tenant_logout` | End school-admin session. |
| `/portal/<schema_name>/dashboard/` | `dashboard` | Admin dashboard. |
| `/portal/<schema_name>/dashboard/mobile/` | `mobile_dashboard` | Mobile dashboard. |
| `/portal/<schema_name>/dashboard/mobile/more/` | `mobile_more` | Mobile navigation/more screen. |
| `/portal/<schema_name>/students/` | `student_list` | Student list. |
| `/portal/<schema_name>/students/mobile/` | `mobile_student_list` | Mobile student list. |
| `/portal/<schema_name>/students/add/` | `add_student` | Add student. |
| `/portal/<schema_name>/students/add/mobile/` | `add_student_mobile` | Mobile add student. |
| `/portal/<schema_name>/students/edit/<student_id>/` | `edit_student` | Edit student. |
| `/portal/<schema_name>/students/<student_id>/` | `student_profile` | Student profile. |
| `/portal/<schema_name>/students/mobile/<student_id>/` | `mobile_student_profile` | Mobile student profile. |
| `/portal/<schema_name>/fee/collection/` | `fee_collection` | Fee collection page. |
| `/portal/<schema_name>/fee/collection/<student_id>/` | `fee_collection` | Collection page preselected for student. |
| `/portal/<schema_name>/fee/collection/mobile/` | `mobile_fee_collection` | Mobile collection page. |
| `/portal/<schema_name>/fee/collection/mobile/<student_id>/` | `mobile_fee_collection` | Mobile collection page for student. |
| `/portal/<schema_name>/fee/receipt/<receipt_id>/` | `fee_receipt` | Receipt. |
| `/portal/<schema_name>/fee/receipt/mobile/<receipt_id>/` | `mobile_fee_receipt` | Mobile receipt. |
| `/portal/<schema_name>/fee/structure/` | `fee_structure` | Grade fee structure. |
| `/portal/<schema_name>/fee/structure/mobile/` | `mobile_fee_structure` | Mobile fee structure. |
| `/portal/<schema_name>/fee/settings/` | `fee_settings` | Fee generation/late-fee settings. |
| `/portal/<schema_name>/fee/settings/mobile/` | `mobile_fee_settings` | Mobile fee settings. |
| `/portal/<schema_name>/fee/family-payment/` | `family_payment` | Guardian/family payment flow. |
| `/portal/<schema_name>/defaulters/` | `defaulters` | Fee defaulters. |
| `/portal/<schema_name>/defaulters/mobile/` | `mobile_defaulters` | Mobile defaulters. |
| `/portal/<schema_name>/reports/` | `reports` | Reports. |
| `/portal/<schema_name>/reports/mobile/` | `mobile_reports` | Mobile reports. |
| `/portal/<schema_name>/settings/` | `settings` | School settings. |
| `/portal/<schema_name>/settings/mobile/` | `mobile_settings` | Mobile settings. |
| `/portal/<schema_name>/stock/` | `stock_management` | Stock list and management. |
| `/portal/<schema_name>/stock/mobile/` | `mobile_stock_management` | Mobile stock list. |
| `/portal/<schema_name>/stock/product/<product_id>/` | `product_detail` | Product detail. |
| `/portal/<schema_name>/stock/product/<product_id>/mobile/` | `mobile_product_detail` | Mobile product detail. |
| `/portal/<schema_name>/stock/category/add/` | `add_category` | Create category. |
| `/portal/<schema_name>/stock/category/delete/<category_id>/` | `delete_category` | Delete category. |
| `/portal/<schema_name>/stock/product/add/` | `add_product` | Create product. |
| `/portal/<schema_name>/stock/product/delete/<product_id>/` | `delete_product` | Delete product. |
| `/portal/<schema_name>/sell/` | `sell_separately` | Separate product sale workflow. |
| `/portal/<schema_name>/sell/mobile/` | `mobile_sell_separately` | Mobile separate sale workflow. |
| `/portal/<schema_name>/vouchers/` | `vouchers_list` | Voucher listing. |
| `/portal/<schema_name>/vouchers/mobile/` | `mobile_vouchers_list` | Mobile voucher listing. |
| `/portal/<schema_name>/fee/logs/` | `fee_logs` | Fee-generation/payment logs. |
| `/portal/<schema_name>/fee/logs/mobile/` | `mobile_fee_logs` | Mobile fee logs. |
| `/portal/<schema_name>/attendance/` | `admin_attendance` | Student/staff attendance administration. |
| `/portal/<schema_name>/leave/` | `leave_management` | Staff leave administration. |

## Tenant-admin JSON/API routes

| Path | Name / owning module | Purpose |
|---|---|---|
| `/portal/<schema_name>/api/fee-collection/` | `fee_collection_list_api` (`fee_collection.py`) | Fee collection data/list. |
| `/portal/<schema_name>/api/receipts/` | `receipt_list_api` (`fee_collection.py`) | Receipt data/list. |
| `/portal/<schema_name>/api/students/` | `student_list_api` (`students.py`) | Student list data. |
| `/portal/<schema_name>/api/products/` | `product_list_api` (`stock.py`) | Product list data. |
| `/portal/<schema_name>/api/student/<student_id>/current-fee-status/` | `student_current_fee_status` (`students.py`) | Student current fee status. |
| `/portal/<schema_name>/api/global-search/` | `global_search_api` (`search.py`) | Tenant-wide search. |
| `/portal/<schema_name>/api/class-strength/` | `class_strength_api` (`classes.py`) | Class enrollment/strength summary. |
| `/portal/<schema_name>/api/student-search/` | `student_search_api` (`students.py`) | Student lookup. |
| `/portal/<schema_name>/api/sync-offline-student/` | `sync_offline_student_api` (`students.py`) | Synchronize offline student entry. |
| `/portal/<schema_name>/api/student/<student_id>/fee-records/` | `student_fee_records_api` (`students.py`) | Student fee-record history. |
| `/portal/<schema_name>/api/student/<student_id>/payments/` | `student_payments_api` (`students.py`) | Student payment history. |
| `/portal/<schema_name>/api/dismiss-notification/` | `dismiss_notification` (`notifications.py`) | Dismiss notification. |
| `/portal/<schema_name>/api/notifications/` | `notifications_list_api` (`notifications.py`) | List notifications. |
| `/portal/<schema_name>/api/notifications/mark-read/` | `mark_notification_read_api` (`notifications.py`) | Mark one notification read. |
| `/portal/<schema_name>/api/notifications/mark-all-read/` | `mark_all_notifications_read_api` (`notifications.py`) | Mark notifications read. |
| `/portal/<schema_name>/api/student/<student_id>/voucher-status/` | `voucher_status_api` (`vouchers.py`) | Voucher status. |
| `/portal/<schema_name>/api/student/<student_id>/generate-voucher/` | `generate_voucher_api` (`vouchers.py`) | Generate a fee voucher. |
| `/portal/<schema_name>/api/student/<student_id>/voucher-html/` | `voucher_html_api` (`vouchers.py`) | Voucher HTML response. |
| `/portal/<schema_name>/api/staff-search/` | `staff_search_api` (`staff.py`) | Staff lookup. |
| `/portal/<schema_name>/api/staff/subject-assignments/` | `staff_subject_assignments_api` (`staff_extras.py`) | Query staff subject assignments. |
| `/portal/<schema_name>/api/staff/assign-subject-teacher/` | `staff_assign_subject_teacher_api` (`staff_extras.py`) | Assign subject teacher. |
| `/portal/<schema_name>/api/staff/unassign-subject-teacher/` | `staff_unassign_subject_teacher_api` (`staff_extras.py`) | Remove subject-teacher assignment. |
| `/portal/<schema_name>/api/staff/class-teacher-management/` | `staff_class_teacher_management_api` (`staff_extras.py`) | Query/manage class-teacher assignments. |
| `/portal/<schema_name>/api/staff/assign-class-teacher/` | `staff_assign_class_teacher_api` (`staff_extras.py`) | Assign class teacher. |
| `/portal/<schema_name>/api/staff/quick-stats/` | `staff_quick_stats_api` (`staff_extras.py`) | Staff summary counts. |
| `/portal/<schema_name>/api/class-strength/` | `class_strength_api` (`classes.py`) | Class strength (also listed above). |

### Class and subject routes

| Path | Name / module | Purpose |
|---|---|---|
| `/portal/<schema_name>/classes/` | `class_management` | Redirects legacy class route to teacher management. |
| `/portal/<schema_name>/teachers/` | `teachers_management` | Class/subject/assignment management. |
| `/portal/<schema_name>/teachers/subjects/` | `teachers_management_subjects` | Subjects tab. |
| `/portal/<schema_name>/teachers/assignments/` | `teachers_management_assignments` | Assignments tab. |
| `/portal/<schema_name>/teachers/class-teachers/` | `teachers_management_class_teachers` | Class-teacher tab. |
| `/portal/<schema_name>/my-classes/` | `classes_management` | Admin class cards. |
| `/portal/<schema_name>/my-classes/<class_id>/` | `class_detailed` | Class detail. |
| `/portal/<schema_name>/my-classes/<class_id>/assign-class-teacher/` | `api_class_assign_class_teacher` | Class page class-teacher assignment. |
| `/portal/<schema_name>/my-classes/<class_id>/assign-subject-teacher/` | `api_class_assign_subject_teacher` | Class page subject-teacher assignment. |
| `/portal/<schema_name>/classes/mobile/` | `mobile_class_management` | Mobile class list. |
| `/portal/<schema_name>/classes/add/` | `add_class` | Add class. |
| `/portal/<schema_name>/classes/edit/<class_id>/` | `edit_class` | Edit class. |
| `/portal/<schema_name>/classes/delete/<class_id>/` | `delete_class` | Delete class. |
| `/portal/<schema_name>/subjects/add/` | `add_subject` | Add subject. |
| `/portal/<schema_name>/subjects/edit/<subject_id>/` | `edit_subject` | Edit subject. |
| `/portal/<schema_name>/subjects/delete/<subject_id>/` | `delete_subject` | Delete subject. |
| `/portal/<schema_name>/assignments/add/` | `assign_subject` | Add class-subject-teacher assignment. |
| `/portal/<schema_name>/assignments/edit/<assignment_id>/` | `edit_assignment` | Edit assignment. |
| `/portal/<schema_name>/assignments/delete/<assignment_id>/` | `delete_assignment` | Delete assignment. |
| `/portal/<schema_name>/classes/assign-teacher/` | `assign_class_teacher` | Assign class teacher. |
| `/portal/<schema_name>/students/teacher/<teacher_id>/` | `students_by_teacher` | Students associated with a teacher. |

### Timetable routes

All are tenant-admin wrapped. Owning modules are in parentheses.

| Path | Name | Purpose |
|---|---|---|
| `/portal/<schema_name>/timetable/` | `timetable_management` | Calendar and timetable page (`timetable.py`). |
| `/portal/<schema_name>/timetable/periods/` | `timetable_periods` | Period/day-schedule setup (`periods.py`). |
| `/portal/<schema_name>/timetable/assign/` | `timetable_assignments` | Assign saved timetables to classes. |
| `/portal/<schema_name>/timetable/assign/submit/` | `api_assign_timetable` | Add class timetable assignment. |
| `/portal/<schema_name>/timetable/assign/unassign/` | `api_unassign_timetable` | Remove class timetable assignment. |
| `/portal/<schema_name>/api/timetable/class/<class_id>/available-timetables/` | `api_class_available_timetables` | Available timetables for a class. |
| `/portal/<schema_name>/timetable/assign-teachers/` | `timetable_assign_teachers` | Configure teachers per timetable slot. |
| `/portal/<schema_name>/api/timetable/teacher-assignments/<class_id>/` | `api_get_teacher_assignments` | Load class teacher grid. |
| `/portal/<schema_name>/api/timetable/teacher-assignments/<class_id>/save/` | `api_save_teacher_assignments` | Save class teacher grid. |
| `/portal/<schema_name>/api/timetable/todays-leave/` | `api_timetable_todays_leave` | Teachers currently on leave. |
| `/portal/<schema_name>/api/timetable/substitute/create/` | `api_timetable_substitute_create` | Create a date-specific substitute. |
| `/portal/<schema_name>/api/timetable/substitute/delete/` | `api_timetable_substitute_delete` | Delete substitute assignment. |
| `/portal/<schema_name>/api/timetable/substitute/records/` | `api_timetable_substitute_records` | List substitute records. |
| `/portal/<schema_name>/api/timetable/periods/break/update/` | `api_timetable_periods_break_update` | Update break configuration. |
| `/portal/<schema_name>/api/timetable/periods/bunch/add/` | `api_timetable_periods_bunch_add` | Add period schedule block. |
| `/portal/<schema_name>/api/timetable/periods/bunch/delete/` | `api_timetable_periods_bunch_delete` | Delete period schedule block. |
| `/portal/<schema_name>/api/timetable/holiday/add/` | `api_timetable_holiday_add` | Add holiday. |
| `/portal/<schema_name>/api/timetable/holiday/delete/` | `api_timetable_holiday_delete` | Delete holiday. |
| `/portal/<schema_name>/api/timetable/holiday/update/` | `api_timetable_holiday_update` | Update holiday. |
| `/portal/<schema_name>/api/timetable/day-schedules/` | `api_timetable_day_schedules` | Save day schedules. |
| `/portal/<schema_name>/api/timetable/day-schedules/batch-update/` | `api_timetable_day_schedules_batch_update` | Batch change label times. |
| `/portal/<schema_name>/api/timetable/labels/list/` | `api_timetable_labels_list` | List schedule labels. |
| `/portal/<schema_name>/api/timetable/labels/add/` | `api_timetable_labels_add` | Add schedule label. |
| `/portal/<schema_name>/api/timetable/labels/update/` | `api_timetable_labels_update` | Rename/update schedule label. |
| `/portal/<schema_name>/api/timetable/labels/delete/` | `api_timetable_labels_delete` | Delete schedule label when unreferenced. |

`api_update_calendar`, `api_add_period`, `api_delete_period`, `api_update_period`, `api_get_timetable`, and `api_save_timetable` are imported from `views/timetable.py` but are not directly attached to a `path()` in the current root URLconf. Confirm registration before assuming those callables have HTTP routes.

### Admin attendance routes

| Path | Name | Purpose |
|---|---|---|
| `/portal/<schema_name>/attendance/` | `admin_attendance` | Attendance admin screen. |
| `/portal/<schema_name>/api/attendance/students/` | `admin_attendance_students_api` | Students/register for marking. |
| `/portal/<schema_name>/api/attendance/mark/` | `admin_attendance_mark_api` | Mark or update one student's attendance. |
| `/portal/<schema_name>/api/attendance/records/` | `admin_attendance_records_api` | Attendance record listing. |
| `/portal/<schema_name>/api/attendance/summary/` | `admin_attendance_summary_api` | Attendance summary. |
| `/portal/<schema_name>/api/attendance/student/<student_id>/history/` | `admin_attendance_student_history_api` | Student attendance history. |
| `/portal/<schema_name>/api/attendance/student/<student_id>/history-paginated/` | `admin_attendance_student_history_paginated_api` | Paginated student history. |
| `/portal/<schema_name>/api/attendance/bulk-mark/` | `admin_attendance_bulk_mark_api` | Bulk attendance marking. |
| `/portal/<schema_name>/api/attendance/compliance/` | `admin_attendance_compliance_api` | Marking compliance. |
| `/portal/<schema_name>/api/attendance/audit/` | `admin_attendance_audit_api` | Attendance audit records. |
| `/portal/<schema_name>/api/attendance/low-defaulters/` | `admin_attendance_low_defaulters_api` | Low attendance students. |
| `/portal/<schema_name>/api/attendance/policy/` | `admin_attendance_policy_get_api` | Read attendance policy. |
| `/portal/<schema_name>/api/attendance/policy/save/` | `admin_attendance_policy_save_api` | Save attendance policy. |
| `/portal/<schema_name>/api/attendance/staff/` | `admin_staff_attendance_list_api` | Staff attendance listing. |
| `/portal/<schema_name>/api/attendance/staff/mark/` | `admin_staff_attendance_mark_api` | Admin staff attendance mark/update. |
| `/portal/<schema_name>/api/attendance/auto-marked-dates/` | `admin_attendance_auto_marked_dates_api` | Dates with system-generated marks. |
| `/portal/<schema_name>/api/attendance/class-teacher-permissions/` | `admin_attendance_class_teacher_permissions_list_api` | List class teacher permissions. |
| `/portal/<schema_name>/api/attendance/class-teacher-permissions/save/` | `admin_attendance_class_teacher_permissions_save_api` | Save a class teacher permission. |
| `/portal/<schema_name>/api/attendance/class-teacher-permissions/bulk-save/` | `admin_attendance_class_teacher_permissions_bulk_save_api` | Bulk save permissions. |
| `/portal/<schema_name>/api/attendance/daily-logs/` | `admin_attendance_daily_logs_api` | Per-class/date logs. |
| `/portal/<schema_name>/api/attendance/recent-summary/` | `admin_attendance_recent_summary_api` | Recent attendance analytics. |

## Staff portal routes

Staff paths are prefixed `/portal/staff/`; tenant identity is taken from the validated staff session rather than the URL. Public exceptions are called out in `StaffTenantMiddleware`; most other paths require a valid staff session and may also enforce staff feature/role policy.

| Suffix | Name | Purpose |
|---|---|---|
| `manifest.json` | `staff_manifest` | Staff PWA manifest. |
| `sw.js` | `staff_service_worker` | Staff-scoped service worker. |
| `offline/` | `staff_offline` | Offline fallback page. |
| `` (root) | `staff_dashboard_root` | Staff dashboard. |
| `login/` | `staff_login` | Staff sign-in. |
| `logout/` | `staff_logout` | End staff session. |
| `biometric/setup/` | `staff_biometric_setup` | Biometric setup page. |
| `dashboard/` | `staff_dashboard` | Staff dashboard. |
| `classes/` | `staff_classes` | Accessible classes. |
| `classes/<class_id>/students/` | `staff_class_students` | Class roster. |
| `students/<student_id>/` | `staff_student_profile` | Student profile. |
| `profile/` | `staff_profile_page` | Staff profile. |
| `profile/change-password/` | `staff_change_password` | Change staff password. |
| `notifications/` | `staff_notifications` | Staff notifications. |
| `biometric/status/` | `staff_biometric_status` | Biometric registration state. |
| `biometric/registration-options/` | `staff_biometric_registration_options` | WebAuthn registration challenge/options. |
| `biometric/register/` | `staff_biometric_register` | Register a credential. |
| `biometric/prepare-login/` | `staff_biometric_prepare_login` | Prepare WebAuthn login challenge. |
| `biometric/complete-login/` | `staff_biometric_complete_login` | Complete WebAuthn login. |
| `biometric/disable/` | `staff_biometric_disable` | Disable/remove biometric credential. |
| `more/` | `staff_more` | Additional staff navigation. |
| `notifications/<notif_id>/mark-read/` | `staff_mark_notification_read` | Mark staff notification read. |
| `api/classes/` | `staff_api_classes` | Staff class data. |
| `api/profile/` | `staff_api_profile` | Staff profile data. |
| `leave/` | `staff_leave_management` | Staff leave page. |
| `leave/apply/` | `staff_leave_apply_api` | Submit leave request. |
| `leave/history/` | `staff_leave_history_api` | Leave history. |
| `leave/policy/` | `staff_leave_policy_api` | Staff-visible leave policy. |
| `leave/cancel/<leave_id>/` | `staff_leave_cancel_api` | Cancel leave request. |
| `attendance/` | `staff_attendance` | Staff attendance page. |
| `api/attendance/students/` | `staff_attendance_students_api` | Accessible class students/register. |
| `api/attendance/mark/` | `staff_attendance_mark_api` | Teacher attendance mark/update. |
| `api/attendance/records/` | `staff_attendance_records_api` | Staff attendance records. |
| `api/attendance/missed-days/` | `staff_attendance_missed_days_api` | Missed attendance days. |
| `api/attendance/copy/` | `staff_attendance_copy_api` | Copy attendance from a prior source. |
| `api/attendance/policy/` | `staff_attendance_policy_api` | Attendance policy view. |
| `api/attendance/dates/` | `staff_attendance_dates_api` | Available attendance dates/permissions. |

## Leave administration routes

| Path | Name | Purpose |
|---|---|---|
| `/portal/<schema_name>/leave/<leave_id>/detail/` | `leave_detail_api` | Leave request detail. |
| `/portal/<schema_name>/leave/<leave_id>/approve/` | `leave_approve` | Approve request. |
| `/portal/<schema_name>/leave/<leave_id>/reject/` | `leave_reject` | Reject request. |
| `/portal/<schema_name>/leave/policy/save/` | `leave_policy_save` | Update tenant leave policy. |
| `/portal/<schema_name>/leave/staff/<staff_id>/summary/` | `leave_staff_summary_api` | Staff leave summary. |
| `/portal/<schema_name>/leave/staff/<staff_id>/suspend/` | `staff_suspend` | Suspend leave applications. |
| `/portal/<schema_name>/leave/staff/<staff_id>/unsuspend/` | `staff_unsuspend` | Lift suspension. |
| `/portal/<schema_name>/leave/staff/<staff_id>/suspensions/` | `staff_suspensions_api` | List suspension history. |

## Method, payload, and security conventions

- The route table shows registration and wrapper status, not complete request schemas. Inspect the view and its matching JavaScript/template for HTTP methods, CSRF behavior, JSON keys, and response status codes.
- Tenant-admin wrapper coverage is broad but not universal. The four root fee/debug utility APIs above are not wrapped in `public_urls.py`; verify their view-level checks before making them internet-facing.
- A few imported callables are not registered as paths; an import alone does not create an endpoint.
- Keep CSRF enabled for browser-authenticated writes. Do not add `csrf_exempt` merely to make a client request work; preserve wrapper metadata using `functools.wraps` when decorators are involved.
- Keep tenant schema selection and authorization separate: validating a schema slug does not establish permission to access it.
