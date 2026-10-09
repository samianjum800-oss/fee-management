# Attendance

## Overview

AXIS supports student attendance for a full day or for individual timetable periods. School administrators can review and correct school-wide records; teachers use the staff portal to mark the classes and periods assigned to them. The administrator can set which past dates teachers may view or edit.

## School administrator: review and mark attendance

1. Open **Attendance** from the school administrator menu.
2. Review the class overview for today's status: **Completed**, **Partial**, **Pending**, or **No Students**.
3. Open the class register you need and choose the date. Check that the displayed class and date are correct.
4. Select a status for each student: **Present**, **Absent**, **Late**, **Half Day**, or **Excused**. A holiday is set from the school calendar, not by marking one student as a holiday.
5. Use a bulk action only when it is correct for every student, then adjust individual exceptions.
6. Save the register and review the confirmation/status message.
7. Use the history, summary, audit, and low-attendance areas to follow up on records or corrections.

## Teacher: take a class register

1. Sign in to the staff portal and open **Attendance**.
2. Choose your class-teacher class, or choose a scheduled subject period if you are a subject teacher.
3. Confirm the date. For the class-teacher full-day register, today is available. Past dates follow the permissions set by the school administrator.
4. Select the correct status for each student. Use **All Present** or **All Absent** only when it is accurate for the whole list.
5. Check the date summary and any lock/quota notice.
6. Choose **Save Attendance**, review the confirmation, and select **Yes, Save**.
7. Use **History** to review previous marks. If the page offers **Edit**, use it only when your class permission and remaining edit count allow the change.

!!! warning "Check the date before saving"
    Attendance changes can affect family follow-up and school reports. Verify the class, date, and each student's status before confirming. Every create or change is attributed and included in an audit trail.

## How teacher access works

| Teacher situation | What the staff portal allows |
|---|---|
| Class teacher marking today | View and edit the full-day register for their assigned class. |
| Class teacher viewing a past date | Depends on the class's backdate setting and view-history window. |
| Class teacher editing a past date | Depends on the backdate setting, edit-history window, and remaining per-date edit allowance. |
| Subject teacher | Mark the teacher's own assigned period for today; does not get the class teacher's full-day editing authority by default. |
| Holiday or vacation date | Attendance marking is blocked when the date is recognized as a holiday. |

The school administrator controls **Backdate Access**, **View History Days**, **Edit History Days**, and **Max Edits Per Date** per class from the attendance permissions controls. Admin edits do not use a teacher's edit quota.

## Staff attendance (administrator)

The administrator attendance area also exposes staff attendance records and a staff-marking action. The record may show check-in/out, status, late minutes, and source. A biometric sign-in can create a staff attendance entry; administrators can review or correct staff records. The teacher's **Attendance** page described above is for student registers, not a personal staff check-in screen.

## What you see

```text
Administrator: class | students | marked today | status | auto-marked history
Teacher home:  Class Teacher classes / Subject periods
Register:      Date | student list | status choices | Save Attendance
History:       Date | present / absent / late / excused | Edit when permitted
```

## System-filled past dates

When an administrator or teacher opens the attendance page, AXIS may fill missing full-day records for recent past, non-holiday dates. The system marks active students as present, or excused when an approved student leave covers the date. These entries are labeled as system-generated; they are not a teacher's manual confirmation. Teachers can edit an auto-marked row when they have permission, and the change is recorded.

!!! note "Approved student leave"
    Approved student leave can cause the covered full-day register to show **Excused**. The current portal navigation does not provide a student/parent leave-application page; ask the school administrator how student leave is entered for your school.

## Desktop and mobile

=== "School administrator"

    Open **Attendance** from the desktop sidebar. The class overview and management controls are designed for an administrator. Use its date, class, staff, policy, and history controls as needed.

=== "Teacher mobile portal"

    Open **Attendance** from the staff portal's bottom navigation. The page shows your class-teacher classes and your own subject periods for today. Tap the relevant class/period to open the register.

## Common scenarios

- **A student arrives late:** Select **Late**, not Present, if the school uses the late status.
- **A student is excused:** Choose **Excused** where permitted, or confirm that approved student leave has been recorded.
- **You forgot yesterday's register:** Ask the administrator to check the class's backdate view/edit rules. The date may be read-only or outside the edit window.
- **An auto-marked entry is wrong:** Open the date, update the student's status if the page allows it, and save with the required confirmation. The correction is audited.
- **The school is closed:** Add the correct holiday/vacation in [Timetable](timetable.md); the register uses those calendar rules.

!!! tip "Keep the class roster current"
    A student must be active and assigned to the correct class for the register to include them. Correct class placement from the [Student profile](students.md) before taking attendance.

## FAQ

### Why can't I edit a past date?
The school administrator may have set past attendance to view-only, limited the allowed history, or the class may have used its edit allowance for that date.

### Why can't I mark attendance today?
Check whether today is a weekly holiday, annual holiday, or vacation. Also confirm you opened a class/period assigned to your staff account.

### Can I mark every student Present at once?
Yes, the staff register includes bulk **All Present** and **All Absent** controls. Review individual exceptions before saving.

### What does an AUTO badge mean?
AXIS filled that past date automatically because no full-day mark was present when its catch-up ran. It is not proof a teacher reviewed the register.

### Does the teacher attendance page record my own work hours?
No. It is the student attendance register. Staff attendance records are managed from the administrator attendance area and may be written by biometric sign-in or an administrator.

## Troubleshooting

| Problem | What to do |
|---|---|
| My class is missing | Check with the administrator that you are assigned as class teacher or subject teacher and that the class is active. |
| The register says locked | Read the displayed reason. Ask the administrator to review the class's backdate permission and edit quota. |
| A holiday banner appears | Confirm the date against the school's weekly/annual holiday and vacation calendar. Do not try to override it by marking one student. |
| A student's status changed automatically | Review the AUTO indicator and approved leave record. Correct the row if permitted and explain the change in the audit/review process. |
| Save did not complete | Check the connection, reopen the class/date, and see whether the status already saved before submitting again. |

## Related guides

[Staff portal](staff-portal.md) · [Timetable](timetable.md) · [Leave management](leave.md) · [Students](students.md) · [Reports](reports.md)
