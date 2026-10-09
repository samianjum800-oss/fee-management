# Reports and defaulters

## Overview

Use **Reports** to review money received during a time period, outstanding balances, payment modes, monthly collection patterns, and students with balances. Use **Defaulters** when you need a focused list of students with unpaid or partly paid fee records.

## Review financial activity

1. Open **Reports** from the school menu or **More** on mobile.
2. Choose a quick period such as **Today**, **This week**, **This month**, **This year**, **Last 6 months**, or **All**.
3. To choose another interval, enter a **Start date** and **End date**, then apply the filter. If the dates are reversed, AXIS swaps them into chronological order.
4. Search the payment list by receipt number, student name, or roll number.
5. Review the collection total, payment count, pending total, collection rate, recent monthly totals, payment-mode breakdown, and the payment rows for the selected period.
6. Open a receipt or student profile to verify the underlying transaction before making a correction.

The page also summarizes balances by grade and highlights students with the largest pending amounts. These summaries are useful for follow-up, but the student fee record is the source for a specific charge.

## Follow up on a defaulter

1. Open **Defaulters**.
2. Search by student/guardian details and optionally filter by grade and section.
3. Use the overdue-days filter to focus on balances older than a chosen number of days.
4. Sort the list by amount or name where available.
5. Open the student's profile or choose the collection action.
6. Contact the family using the school's normal process, then record any received payment in [Fee Collection](fees.md).

```text
Reports
[Today] [Week] [Month] [Year] [Last 6 months] [All]
[Start date ____] [End date ____] [Apply]
Collection total | Pending total | Payment count | Collection rate
Charts: monthly collection / payment mode / pending by grade
Payments: [Search receipt, student, or roll number]
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

### Can I download the report as a spreadsheet?
The current Reports screen provides on-page summaries, charts, and a paginated payment list. It does not expose a report-download control in the user interface.

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
