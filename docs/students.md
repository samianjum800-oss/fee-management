# Student records

## Overview

Use **Students** to find, add, update, and review a student's school record. Each record can include guardian details, class placement, admission details, status, and a student-specific fee. AXIS assigns a roll number when a new student is saved.

## Find a student

1. Open **Students** from the desktop menu, or tap **Students** on mobile.
2. Search by the student's name, roll number, guardian name, or guardian CNIC when those fields are available.
3. Narrow the list using the displayed class/grade, section, or status filters.
4. Open the student's name or profile action to view their record, fees, and payment history.

```text
Students
[Search name / roll number] [Class] [Section] [Status] [Filter]
Name              Roll no.     Class / section       Status
Student example   assigned     Grade 4 - A           Active
```

## Add a student

1. From the student list, choose **Add Student**.
2. Enter the student's name and guardian information, including the father's name, CNIC, and mobile number.
3. Choose the class. For a wing school, select the correct **Campus / Wing** first; the class list is filtered to that campus.
4. Complete the admission date, status, and any optional details such as gender, date of birth, address, or notes.
5. Review **Custom Fee**. Leave the normal class fee in place unless this student has an approved exception.
6. Choose **Save Student**. AXIS assigns a roll number and confirms the new record.
7. Open the profile and verify the class, section, guardian contact, and fee before moving on.

!!! note "Class placement controls the displayed grade"
    When a class is selected, AXIS derives the student's grade and section from that class. In wing schools, the campus/wing is included in the displayed class label.

## Edit a record

1. Search for the student and open their profile.
2. Choose the edit action.
3. Update the needed fields and select the correct class/wing.
4. Review any custom fee change carefully, then choose **Update Student**.
5. Return to the profile and confirm the update.

Student status options include **Active**, **Suspended**, and **Graduated**. Use a status change to reflect the student's current enrollment; the student form does not provide a delete action.

## Mobile and offline entry

=== "Desktop"

    The desktop list offers wider filters and a profile view. Use the search box and class/status filters to narrow the list before opening a record.

=== "Mobile"

    Tap **Students** at the bottom, then use **Add Student** or open a student card. The form uses the same required school and class information in a compact layout.

    Supported browsers can queue student create/edit data in the browser when an entry is saved offline. When the connection returns, AXIS attempts to send the queued entry to your school's portal. Keep the device and browser profile available until synchronization completes.

!!! warning "Check queued entries"
    Offline entries are held in the browser on that device. Do not clear browser storage, use private browsing, or assume an entry is on the school server until the portal confirms synchronization. If an entry fails to sync, reconnect and contact the school administrator before entering it again to avoid duplicates.

## Common scenarios

- **A student moves to another section:** Edit the student, choose the new class, save, and verify the displayed grade/section.
- **A student receives a fee concession:** Set the approved student-specific custom fee and check the next generated fee record.
- **A student has left the school:** Change the student's status to the appropriate non-active option instead of trying to delete the record.
- **A wing-school class is missing:** Confirm the campus/wing exists in [School settings](school-settings.md), then verify the class is active in [Classes and staff](classes-and-staff.md).

## FAQ

### Does AXIS choose the roll number?
Yes. If you do not enter a roll number, AXIS assigns one when it saves the student. Check the saved profile for the final value.

### Can I upload a student photo from this form?
The current student form does not include a photo field. Do not expect a file selected elsewhere to be saved as the student's photo.

### Does changing a student's custom fee change old fee records?
It changes the student's fee setting for future generation. Review existing fee records separately; do not assume past vouchers are rewritten.

### Why can't I select a class?
The form only offers active classes. For a wing school, select the matching campus/wing; a class in a different wing will not be available in that selection.

## Troubleshooting

| Problem | What to do |
|---|---|
| Duplicate or wrong student appears | Search by roll number and guardian CNIC before adding a second record. Ask an administrator to resolve duplicates. |
| Class/section on profile is unexpected | Edit the student and verify the selected `Class`; the saved class determines grade and section. |
| Custom fee is not used on a voucher | Check the student's custom fee and the matching grade fee structure, then inspect the actual month's fee record. |
| Offline entry is missing | Reconnect on the same device/browser, open the student form or student list, and allow synchronization to run. Confirm the record exists before retrying. |
| Save shows field errors | Correct the fields named in the form; check dates, CNIC/contact values, and campus/class consistency. |

## Related guides

[School settings](school-settings.md) · [Fees and vouchers](fees.md) · [Classes and staff](classes-and-staff.md) · [Reports](reports.md)
