# Timetable and periods

## Overview

Build a timetable in three stages: set the academic calendar and day slots, create a reusable periods timetable, assign it to classes, and then place subjects/teachers into the period slots. Setting holidays and vacations here also helps AXIS decide when attendance should not be marked.

## Step 1: Set the academic calendar

1. Open **Time-Table**.
2. Review the school's working days and school start/end times.
3. Use the day-schedule table to add a slot for each day/shift you need. Choose the reusable label, start time, end time, number of periods, and period duration.
4. If the day has a break, set where it falls and how long it lasts.
5. Use **Manage Labels** to create labels such as `Morning` or `Senior`. Use **Edit Timing** to batch-adjust times for a label when needed.
6. Review the table and the save status before leaving the page. Calendar edits are saved automatically.

!!! warning "Calendar changes affect saved timetables"
    Changing or removing a day slot can alter existing periods timetables. The screen warns that time changes can remove a day from affected timetables and period-count changes can recalculate its periods. Review all affected classes after changing the calendar.

## Step 2: Create a periods timetable

1. Open **Periods** from the Time-Table menu.
2. Choose **Create New Timetable**.
3. Give the timetable a clear title and select its schedule label.
4. Choose the school days/slots and review the generated start/end times and period count.
5. Set the break position and duration if needed.
6. Save the timetable and review its displayed weekly grid.

A saved timetable is a reusable pattern; it is not assigned to a class until you complete the next step.

## Step 3: Assign the timetable to classes

1. Open **Assign to Classes**.
2. Choose a class and one of the saved periods timetables, then submit the assignment.
3. Repeat for other classes and review the assignment list.
4. If a class needs more than one timetable, assign additional patterns only when they use the same schedule label. AXIS does not allow a second timetable with a different label for that class.
5. To remove one, use its unassign action and confirm the class assignment list afterward.

## Step 4: Assign subjects and teachers to periods

1. Open **Assign to Teachers**.
2. Choose **Assign Periods to Teachers**, select a class that already has a timetable, and wait for its period grid to load.
3. For each period, select the subject and teacher. The subject must already be connected to the class and an active teacher in **Classes & Subjects**.
4. Read any conflict warning. A teacher already assigned at the same day and period in another class is not free for that slot.
5. Choose **Save Assignments** and confirm the assigned-period count.
6. Use **See Records** to review date-specific substitute assignments where available.

```text
Time-Table: calendar + holidays
             |
             v
Periods: create a labelled timetable
             |
             v
Assign to Classes: connect timetable to class
             |
             v
Assign to Teachers: subject + teacher per period
```

!!! tip "Use clear timetable titles"
    Include the shift or audience in the title, for example `Junior Morning`. This makes the right pattern easier to choose when assigning it to a class.

## Holidays and vacations

- **Weekly Holidays:** choose a day and label, such as Saturday or Sunday.
- **Annual Holidays:** enter the month/day and a name for a recurring date.
- **Vacations:** enter a name, start date, end date, and optional description.

Check these dates before the school year begins. Attendance pages use the calendar to prevent marking on holidays, and leave quota settings may use weekly holidays when counting working days.

## Desktop and mobile

=== "Desktop"

    Use the separate Time-Table, Periods, Assign to Classes, and Assign to Teachers pages. Wide teacher grids are easier to review on a desktop.

=== "Mobile"

    Mobile navigation can open timetable pages, but editing a calendar grid or assigning many period slots is easier on a larger screen. If a period or teacher column is clipped, rotate the device or continue on desktop.

## Common scenarios

- **Create a new school shift:** Add a new schedule label and day slots, create a timetable using that label, then assign it to matching classes.
- **Change a teacher for one period:** Update the teacher assignment grid and save. Check the conflict message before choosing a replacement.
- **A teacher is absent today:** Check the approved leave list and create a date-specific substitute for a free, qualified teacher. This changes that date only; it does not permanently alter the timetable.
- **School adds a weekly holiday:** Add it under Weekly Holidays and review attendance and leave rules that count working days.

!!! note "Substitutes are date-specific"
    A substitute covers a scheduled slot for a particular date. It does not replace the normal subject/teacher assignment for future weeks.

## FAQ

### Why is a class missing from Assign to Teachers?
The class needs an active periods timetable assignment first. Go to **Assign to Classes**, assign a pattern, then return.

### Why is a timetable not available for a class?
If a class already has an assigned pattern, additional patterns must use the same schedule label. The exact same pattern cannot be assigned twice.

### Why can't I select a teacher for a subject?
The subject needs an active class assignment and the teacher must be active. Set these up in [Classes and staff](classes-and-staff.md).

### Does changing the calendar update assigned timetables?
It can adjust existing patterns. Read the warning on the Time-Table page and review affected classes after saving.

### Can I use a timetable as a one-day substitute?
No. Use the substitute/fixture action on Assign to Teachers for date-specific coverage.

## Troubleshooting

| Problem | What to check |
|---|---|
| No periods are generated | Confirm the academic calendar has active day slots, valid start/end times, a label, and at least one period. |
| The wrong class schedule appears | Review the class's timetable assignment and label. Avoid assigning patterns from different labels to one class. |
| A teacher conflict appears | Check the teacher's other class assignments for the same day and period; choose an available teacher or revise the intended slot. |
| Calendar edit changed an existing pattern | Open Periods and inspect the saved timetable, then review class assignments and teacher slots. |
| Substitute list is empty | Confirm an approved staff leave covers today and the class has a valid schedule. The replacement must be active, free at that time, and qualified for the subject. |

## Related guides

[Classes and staff](classes-and-staff.md) · [Attendance](attendance.md) · [Leave management](leave.md)
