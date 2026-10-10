# Classes, subjects, and staff

## Overview

AXIS has two related administration areas: **Classes Management** for class records and class details, and **Classes & Subjects** (the **Teachers** page) for the subject catalogue, teacher assignments, and class-teacher assignments. **Staff Management** is where administrators create staff accounts and manage their status and credentials.

## Set up classes

1. If this is a wing school, make sure campuses/wings already exist in [School settings](school-settings.md).
2. Open **Classes Management** to view the school's active class cards. Choose the add-class control.
3. For a wing school, select the campus/wing. Enter the class name and section, then save.
4. Open a class card to view its student roster and details.
5. Use the **Timetable** action on a class card to open that class's periods timetable.
6. Use **Fee Structure** to filter classes by whether a monthly fee is set, and set or edit fees without leaving class management. Use **View class** to open that class's details.
7. In a wing school, use **Campus Management** to add or update campuses and wings from this page.
8. To change a class, use its edit action. To stop using a class, use the deactivate action; this is not the same as deleting its students.
9. Add or move students from each student's [profile](students.md).

Class names are normalized by AXIS. A class name and section must be unique within the selected wing; the same class label may be used under another wing.

## Add subjects and connect teachers

1. Open **Classes & Subjects** (the **Teachers** page). The page has **Subjects**, **Assignments**, and **Class Teachers** tabs.
2. In **Subjects**, add the school's subject names.
3. In **Assignments**, choose a class and subject, then select an active teacher if one is available. Save the assignment.
4. In **Class Teachers**, choose the class and assign its class teacher.
5. Review the class detail page or teacher profile to confirm the assignment.

A subject may only be assigned once to a class. A staff member must be active to appear in assignment pickers. AXIS also uses subject-teacher assignments when building timetable options and staff access.

## Add a staff member and provide their sign-in

1. Open **Staff Management** and choose **Add Staff**.
2. Enter the person's name, job title, department, and any relevant contact or employment details. Save the form.
3. AXIS creates a staff ID and staff portal credential. On desktop, copy the generated username/password shown after saving; the staff profile also shows the credential to the school administrator.
4. Send the staff member the staff portal link and their credentials privately. Ask them to sign in and complete biometric setup if AXIS requests it.
5. Open the staff profile to check their role, status, assigned classes/subjects, and biometric setting.

!!! warning "Credentials are private"
    Staff accounts are individual. Share the first password directly with the staff member, and do not post it in a class group or in a public document. Ask the staff member to change it after first sign-in.

## Manage an existing staff account

- **Edit profile:** Open the staff member and choose Edit.
- **Deactivate:** Change status to inactive. AXIS signs the staff member out of active sessions.
- **Force logout:** Use the profile's logout action to end active sessions without changing the password.
- **Reset password:** Enter and confirm a new password. The administrator reset requires at least 12 characters, an uppercase letter, a digit, and a symbol from `!@#$%^&*`. AXIS signs that staff member out of all devices after reset.
- **Biometric login:** The school administrator can enable or disable the per-staff biometric requirement from the staff profile. This is separate from whether a device has a registered passkey.

```text
Classes & Subjects
[Subjects] [Assignments] [Class Teachers]
Class / Wing       Subject          Teacher           [Edit]
Grade 4 - A        Mathematics      Teacher name

Staff Management
[Search/filter staff] [Add Staff]
Staff profile: personal details | class/subject assignments | login status
```

## Desktop and mobile

=== "Desktop"

    Use **Classes Management** for the class-card view and **Classes & Subjects** for the three assignment tabs. The staff list includes search and filters for department, status, class, and section.

=== "Mobile"

    Use **More** for Classes or Staff. Class and staff forms are compact; on some mobile staff forms, generated credentials are not displayed in the success message. Open the saved staff profile from the administrator account to review or reset credentials.

## Common scenarios

- **A new school year starts:** Review active classes, add new sections, update subject assignments, and confirm each active class has the intended class teacher.
- **A teacher changes classes:** Update the subject/class assignment and class-teacher assignment. Then review [Timetable](timetable.md) teacher slots.
- **A teacher leaves the school:** Deactivate the staff account to stop portal access; do not delete the profile if you need to preserve attendance or assignment history.
- **A staff member cannot log in:** Confirm they are active, check the username from their profile, reset the password if needed, and check the biometric setting. See [Staff portal](staff-portal.md).

!!! tip "Review assignments together"
    A class teacher and a subject teacher have different responsibilities in AXIS. Confirm both the class-teacher tab and the subject assignments before staff begin attendance or timetable work.

## FAQ

### Does deactivating a class remove its students or timetable?
No. Class deactivation keeps the class record and its linked students, timetable, teacher assignments, and other class settings. Adding the same class name and section in the same wing restores that class and its existing links rather than creating a blank class.

### Does deleting a subject erase prior attendance or timetables?
Subjects are deactivated from the management workflow. Review linked assignments and timetable use before changing the catalogue.

### Why can't I choose a teacher in an assignment?
Only active staff appear. Create/activate the staff account first, then return to the assignment page.

### Can one teacher be a class teacher for multiple classes?
The class-teacher management interface may move a teacher from an existing class when assigning them to a new class. Review the displayed assignments before saving.

### Why does the staff member see only some classes?
The staff portal shows classes connected to that staff member as class teacher or subject teacher. Check their class and subject assignments.

## Troubleshooting

| Problem | What to do |
|---|---|
| Duplicate class/subject error | Search the current catalogue first. Class duplicates are checked by class name, section, and wing; subject names are checked without regard to case. |
| Campus does not appear in class form | Add/activate it under School Settings, then refresh the class page. |
| Staff credential is not visible after mobile creation | Open the staff profile from desktop or reset the password there. |
| Teacher can sign in but sees no classes | Verify active class-teacher or subject-teacher assignments and that the staff portal feature is enabled. |
| Deactivated staff still appears in old records | Historical records remain; inactive status blocks normal access but does not erase history. |

## Related guides

[School settings](school-settings.md) · [Students](students.md) · [Timetable](timetable.md) · [Attendance](attendance.md) · [Staff portal](staff-portal.md)
