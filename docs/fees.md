# Fees, payments, receipts, and vouchers

## Overview

The fee tools help your school set class-level monthly amounts, generate monthly student fee records, collect full or partial payments, record a payment method, and review a receipt. AXIS also supports family payments by guardian CNIC and lets you add stock items to a student's collection in the same payment flow.

## Set a monthly fee for a class

1. Open **Fee Structure**.
2. Choose a class. For a wing school, select the campus/wing and then the class.
3. Enter **Monthly Fee** and choose **Save Fee**.
4. Review the class and amount in **Current Fee Structure**.
5. To change it later, choose **Edit**, enter the revised amount, and select **Update Fee**.

!!! warning "Changing a class fee has a broad effect"
    Saving a fee structure updates the custom fee value for students whose saved grade matches that structure. Existing monthly fee records are separate; check any already-generated or paid records before making a change.

## Configure fee generation

1. Open **Fee Settings**.
2. Set the **Fee Generation Day** of the month.
3. Set the **Due Date Offset** (days after generation) and **Late Fee Penalty** if your school uses them.
4. Add or remove default extra charges if they should appear on future fee records.
5. Choose **Save Settings** (or the equivalent save button on your layout).
6. Use the automation control only after your school has agreed how fee generation is scheduled. Review **View Logs** to check previous generation results.

!!! note "Automation needs a scheduled service"
    The page stores the school's automation preference. AXIS also needs the fee-generation job to be configured by the service operator. If you enable automation but no fees appear on the expected date, ask your AXIS administrator to check the schedule; do not repeatedly generate the same month.

## Collect a payment for one student

1. Open **Fee Collection**.
2. Find the student using name, roll number, guardian details, or the available grade/section filters.
3. Choose the student to open **Collect Fee**. Review the student's identity and **Pending Fee Records**.
4. Enter **Amount Received** and choose the payment mode: Cash, Bank Transfer, Cheque, or Online.
5. To include stock items, choose **Add Items**, search or filter by category, add the requested quantities, then choose **Done**. Check stock availability and the item total.
6. Review **Total Due** and **Remaining After Payment**.
7. Choose **Process Payment** once the amount and student are correct.
8. AXIS records the payment and opens the receipt. Review the receipt number and amount before giving it to the payer.

AXIS applies the received amount to the oldest pending/partial/overdue fee records first. If items were selected, any remaining amount is then applied to those items. The stock quantity is reduced when the payment is saved.

!!! warning "Avoid entering more than the amount due"
    The collection screen warns about an amount above the total due, but the current server flow can still record the payment. Confirm the amount before selecting **Process Payment** and resolve any overpayment with your school's finance procedure.

!!! info "Online is a recorded payment mode"
    Selecting **Online** records the method on the transaction. This page does not itself charge a card or connect to an online payment gateway.

## Take a family payment

1. Open **Family Payment**.
2. Enter the father's CNIC exactly as recorded on the students' profiles.
3. Leave **Amount to Pay** blank to pay the full pending amount for the matching active students, or enter a smaller amount.
4. Choose the payment mode and add an optional remark.
5. Review the amount, then choose **Process Payment**.

AXIS spreads a partial family payment across due records in due-date order and creates payment entries for the children whose records were paid. An amount larger than the family's total pending balance is rejected.

## Review vouchers and receipts

- **Vouchers** lists generated fee records for review. A voucher is not evidence that a payment has been made.
- A student's profile shows fee records and payments; use the individual student's fee action to generate the current month's record where available.
- The receipt opens after a successful payment and can be revisited from payment history/reports.
- **Fee Logs** shows fee-generation activity, including records created and skipped.

```text
Fee Collection
[Search/filter students with pending balances]
Student              Pending total          [Collect]

Collect Fee: Student / Roll No.
Pending records + due dates       Amount Received [____]
                                  Payment Mode    [____]
                                  [Add Items] [Process Payment]
```

## Desktop and mobile

=== "Desktop"

    Use the full pending-student list, filters, and the detailed collection drawer. The receipt opens as a full page.

=== "Mobile"

    Tap **Collect** on the bottom menu. Search for a student, review the pending balance, enter the amount, and use **Add Items** if needed. Mobile receipts use a compact layout; check the receipt number and total before handing it over.

## Common scenarios

- **A parent pays less than the full balance:** Enter the amount received. AXIS records a partial payment and leaves the remaining balance open.
- **A parent pays for siblings:** Use Family Payment with the recorded guardian CNIC and the agreed amount.
- **A student buys school supplies while paying fees:** Add the stock items during the student's collection. Check quantity and price before saving.
- **A new monthly voucher is needed:** Confirm fee settings and class/student fee first, then generate the record once and verify it on the student profile or Vouchers page.
- **A payment method was recorded incorrectly:** Keep the receipt and contact the finance administrator; do not create a second payment to compensate without reconciling the first.

## FAQ

### Does saving a fee structure update vouchers already generated?
No. It updates the fee setting for matching students. Review each existing fee record separately; do not assume an issued or paid record changes.

### Can I edit a fee record after payment?
The single-student generation flow blocks changes when the current month's fee has already received a payment. Contact the finance administrator if an issued record needs correction.

### Why did AXIS skip a student during fee generation?
The student may already have a record for that month or may have no positive fee amount/fee structure. Check the fee log and the student's class/custom fee.

### Does a receipt mean the payer used an online gateway?
No. A receipt confirms that AXIS recorded a payment. The selected mode is a label such as Cash or Online.

### Why is a selected item unavailable?
Only products with stock available are offered in the collection drawer. Check Stock Management and do not collect an item that is out of stock.

## Troubleshooting

| Problem | What to do |
|---|---|
| Student does not appear in collection search | Check the spelling, roll number, and whether the student has a pending balance. Review the student profile. |
| Amount due differs from expected | Open the fee record and review base amount, extra charges, late fee, paid amount, and due date. |
| Family CNIC finds no students | Compare the entered CNIC with each active child's student profile. |
| Receipt did not open | Return to Fee Collection or Reports, find the payment, and open its receipt. Do not submit the payment again until you confirm whether the first transaction was saved. |
| Fee automation did not run | Check Fee Logs and ask the service administrator to confirm the scheduled generation job. |
| Stock did not reduce as expected | Verify the payment receipt includes the item and quantity; ask the stock/finance administrator to reconcile the transaction. |

## Related guides

[Students](students.md) · [Reports and defaulters](reports.md) · [Inventory and sales](inventory.md) · [School settings](school-settings.md)
