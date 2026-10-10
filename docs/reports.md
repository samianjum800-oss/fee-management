# Reports and defaulters

## Overview

Use **Reports** as the school's operational overview: financial activity, enrolment, attendance, staff portal presence, leave requests, inventory, sales, attendance changes, and fee-generation runs. The report sections share a date range where the underlying records are dated. Current enrolment, stock, and online presence are snapshots and are not historical values.

## Review financial activity

1. Open **Reports** from the school menu.
2. Choose **Today**, **Yesterday**, **This Week**, **7 Days**, **30 Days**, **This Month**, **This Quarter**, **This Year**, **Last 6 Months**, or **All Time**. You can also enter a custom start and end date. Reversed custom dates are reordered automatically.
3. Use the section links to jump between school overview, attendance, staff portal, leave, inventory and sales, audit history, financial trends, transactions, and defaulters.
4. Search transactions by receipt number, student name, or roll number. **Download CSV** exports the matching collection transactions with the selected date and search filters; **Print report** opens the browser's print dialog.
5. Open student or staff profiles from report rows to inspect the underlying records before taking action.

The page summarizes balances by grade, highlights students with the largest pending amounts, reports student and staff attendance, lists recent leave requests and attendance changes, and flags products with five or fewer units. Use the linked student/staff profile or the source module to verify a specific record before correcting it.

## Report sections and definitions

- **School overview:** current student status counts and academic structure totals.
- **Attendance:** entries in the selected dates. Present, late, and half-day count toward the attendance rate; absent entries are the denominator's other side, and excused/on-leave entries are excluded. Period-based student marks count as separate entries, not unique students.
- **Staff portal:** current online session signal and the latest successful sign-in timestamp. The application does not currently record a page-by-page staff activity log, so this section does not claim to show one.
- **Leave:** staff and student requests created in the selected dates, with recent request rows and status totals.
- **Inventory and sales:** product quantities and estimated retail stock value are current snapshots. Stock value uses selling price, not purchase cost. Sales totals use sale lines attached to payments in the selected dates.
- **Audit and fee generation:** attendance changes and fee-generation runs recorded in the selected dates.
- **Financial trends:** collection and payment-mode summaries. Pending balances are current outstanding amounts, not limited to the selected dates.

The online indicator reflects the staff session signal and its expiry. A sign-in timestamp is not proof that someone is still using the portal; use the attendance record and staff profile for operational follow-up.

## Attendance deep dive

Open **Attendance report** from the Reports page to visit `/portal/<school>/reports/attedence/`. Choose a date range, campus, wing, class, section, source, or period. The page compares campus/wing/class rates, shows daily trends and marking sources, and provides expandable student-level and individual-record tables. Student profiles, class pages, and the attendance-management page are linked from the relevant rows.

Use **Download filtered CSV** to export individual marks with date, student, class, period, status, source, marker, and remarks. For a single selected date, the page also lists active classes without a full-day mark; period-only marks do not count as a full-day completion.

The attendance assistant currently provides private, deterministic insights from the visible report data; there is no configured generative-AI provider. Questions and student data stay in the browser. The reported attendance rate is based on recorded marks, not scheduled school days; period-based marks count as separate entries.

## Follow up on a defaulter

1. Open **Defaulters**.
2. Search by student/guardian details and optionally filter by grade and section.
3. Use the overdue-days filter to focus on balances older than a chosen number of days.
4. Sort the list by amount or name where available.
5. Open the student's profile or choose the collection action.
6. Contact the family using the school's normal process, then record any received payment in [Fee Collection](fees.md).

```text
Reports
[Today] [Yesterday] [Week] [7 Days] [30 Days] [Month] [Quarter] [Year] [Last 6 months] [All]
[Start date ____] [End date ____] [Apply]
Sections: overview / attendance / staff portal / leave / inventory / audit / finance
Collection | balances | attendance | staff sessions | leave | stock & sales | audit
Payments: [Search receipt, student, or roll number] [Download CSV] [Print]
```

!!! note "Date period versus pending balance"
    The selected report dates filter payments collected in that period. Outstanding fees are balances that remain due now. A fee can be overdue even if it was generated outside the selected report period.

## Desktop and mobile

=== "Desktop"

    Use the full report filter row, charts, and payment table. Scroll horizontally on a narrow window to see all payment columns.

=== "Mobile"

    Open **More** and choose **Reports** or **Defaulters**. Use the period filters and search controls, then open the student's profile/collection page to act on a balance.

## Common scenarios

- **Prepare a weekly cash-up:** Choose **This week**, review totals and payment modes, then reconcile the detailed payment rows against your records.
- **Find families to contact:** Open **Defaulters**, set a minimum overdue age, and use the name/guardian filters.
- **Check a disputed payment:** Search by receipt number, open the recorded receipt, and compare date, amount, mode, and remarks.
- **Compare grade balances:** Use the pending-by-grade summary, then open the relevant students to review individual fee records.

!!! tip "Reconcile before contacting a family"
    A pending balance may be reduced by a recent partial payment. Refresh Reports and check the latest receipt before asking a family to pay again.

## FAQ

### What does Download CSV include?
It exports collection transactions matching the selected date range and payment search. Operational summaries remain on the page and are not included in that CSV.

### Why does the payment table show only some payments?
The list is paginated and filtered by the selected dates and search. Clear the search or choose a wider period to see more rows.

### Why is a student listed as a defaulter after paying part of the fee?
A partial payment leaves a remaining balance. Open the student's fee records to see the original amount, amount paid, and amount remaining.

### Does the collection rate mean all billed fees were paid?
It is a summary calculated from recorded collections and pending fee amounts. Use the student fee records and payment receipts for an individual reconciliation.

## Troubleshooting

| Problem | What to check |
|---|---|
| No payments appear | Clear the search, widen the date range, and confirm payments were saved with the expected payment date. |
| A student is missing from Defaulters | Confirm there is a pending, partial, or overdue fee record and a positive balance. |
| A total differs from a receipt | Verify the selected report dates and check whether you are comparing payments collected versus fees billed. |
| Charts are blank | Refresh the page and check the date filter. If the table works but charts do not, ask the administrator to check the browser's network access. |

## Related guides

[Fees and vouchers](fees.md) · [Students](students.md) · [Dashboard](dashboard.md) · [Inventory and sales](inventory.md)
