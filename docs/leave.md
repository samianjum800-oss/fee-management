# Staff leave management

## Overview

The Leave Management feature handles staff leave requests. Staff members submit requests from the staff portal and can review status/history. School administrators review pending requests, set the school's shared leave rules, view usage, and manage suspensions.

## Staff: submit and track a request

1. Sign in to the staff portal and open **More** → **Leave** (or **Leave Management**, depending on the screen).
2. Review the leave rules, used days, remaining weekly/monthly allowance, and any current suspension or approved leave banner.
3. Choose **Apply** or the new-request control.
4. Enter a short title, select the leave type, explain the reason, and choose the start and end dates.
5. Check the dates and policy summary, then submit the request.
6. Open **History** to see whether the request is Pending, Approved, Rejected, or Cancelled. Open a request to read administrator remarks.
7. If a request is still pending or approved and you need to withdraw it, choose its cancel action and confirm.

Leave types include Casual, Sick, Annual, Emergency, and Other. Your school may set different limits, working-day rules, and backdating permissions.

## Administrator: review a request

1. Open **Leave Management** from the school administrator menu.
2. Use search, status, and leave-type filters to find a request. Pending requests are counted in the summary at the top.
3. Open the request details and review staff member, dates, type, reason, current leave usage, and any overlap.
4. Choose **Approve** or **Reject** only after reviewing the request. Add optional remarks and confirm.
5. Check the request status after the action. Approved staff leave is reflected in the staff attendance record for its date range.

## Set school-wide rules

1. On the admin Leave Management page, choose **Policy Settings**.
2. Set the maximum leave days per month, per week, and consecutive days.
3. Choose whether backdated requests are allowed.
4. Choose whether only approved requests count toward the quota, and whether weekly holidays are excluded from the count.
5. Set the rejected-request threshold for automatic suspension, or use `0` to turn that automatic rule off. Set the suspension duration.
6. Choose **Save Policy** and review the updated policy.

## Manage suspensions

1. Choose **Suspensions** on the admin Leave Management page.
2. Review current and past entries before changing one.
3. To add a manual restriction, choose **Suspend staff manually**, select the staff member, enter an optional reason, and set a duration in days.
4. A duration of `0` means no end date: the restriction stays until an administrator lifts it.
5. Use the lift/unsuspend action when the restriction should end early.

```text
Staff portal:  Leave rules | remaining this week/month | Apply | History
Admin portal:  Total / Pending / Approved / Rejected
               Search + Status + Type filters
               Request card: View | Approve | Reject
               Policy Settings | Staff Usage | Suspensions
```

!!! warning "Suspension blocks new applications"
    A suspended staff member cannot submit another request until the suspension ends or an administrator lifts it. Check the selected staff member, duration, and reason before confirming a manual suspension.

!!! note "Working days affect quotas"
    When the working-day option is enabled, weekly holidays from the timetable are excluded from monthly/weekly leave totals. Keep the school's [Timetable](timetable.md) holiday setup current.

## Desktop and mobile

=== "Administrator"

    Use the desktop **Leave Management** page to filter requests, open details, approve/reject, review staff usage, and manage the policy/suspension modals.

=== "Staff member"

    Use the mobile staff portal's **Leave Management** page. The page shows current policy and quota information, request/history tabs, and any active leave or suspension notice.

## Common scenarios

- **Staff request is waiting:** It remains pending until an administrator reviews it. Contact the administrator if the dates are urgent.
- **A request is rejected:** Read the remarks, check the remaining quota, then discuss a revised date range with the administrator before submitting again.
- **Dates are blocked:** The request may be backdated while backdating is disabled, overlap another request, exceed consecutive/monthly/weekly limits, or fall under a suspension.
- **A staff member is away:** Approving their leave marks corresponding staff attendance as On Leave and can also appear in substitute-planning views.
- **A rejection threshold is reached:** If automatic suspension is enabled, AXIS can suspend new requests for the policy duration. The administrator can review and lift the suspension.

!!! tip "Use the date range that reflects the actual absence"
    Requests are checked for overlaps and quotas across their covered dates. Correct dates before submitting rather than sending several overlapping requests.

## FAQ

### Do pending requests use my quota?
It depends on the school's **Count only APPROVED leaves** policy. Rejected and cancelled requests are not counted. The page shows the current policy and remaining allowance.

### Can I request a past date?
Only if the administrator allows backdated leave. If it is disabled, the start date cannot be earlier than today.

### Can I cancel an approved request?
The staff portal permits cancellation of pending or approved requests. Contact the administrator if attendance has already been prepared for those dates so it can be reviewed.

### Why does the number of leave days differ from calendar days?
The policy may count working days only and exclude the school's weekly holidays. The maximum consecutive-day rule still applies to the date span.

### Is student leave requested here?
No. This page is for staff. Ask the school administrator how the school records student leave; approved student leave may be reflected as Excused in [Attendance](attendance.md).

## Troubleshooting

| Problem | What to do |
|---|---|
| Apply button reports a quota error | Check weekly/monthly remaining days, working-day rules, and maximum consecutive days. Adjust the date span with the administrator. |
| Request overlaps another leave | Open History and check pending/approved requests that cover any of the same dates. |
| Backdated start date is rejected | Ask the administrator to review the school's backdate policy; do not change the device date. |
| You see a suspension notice | Check the end date and reason. For a permanent/incorrect suspension, contact the school administrator to review or lift it. |
| Admin cannot find a request | Clear status/type filters, check the search spelling, and use the page controls to move through the request pages. |

## Related guides

[Staff portal](staff-portal.md) · [Attendance](attendance.md) · [Timetable](timetable.md) · [Classes and staff](classes-and-staff.md)
