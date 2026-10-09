# Account security and suspected compromise

## Overview

This guide is for school administrators and staff who suspect someone else has accessed an AXIS account, lost a device, or cannot use a required passkey. Act quickly, use a device you trust, and tell the right administrator. AXIS has separate school-admin and staff accounts, so use the response for the account that may be affected.

!!! danger "Treat unexpected access as urgent"
    If you see a payment, student change, attendance mark, staff change, or sign-in you did not make, stop sharing credentials, preserve the time and details, and contact the school administrator or AXIS service contact immediately. Do not delete records to hide or reverse evidence.

## First response: everyone

1. Stop using the possibly compromised device for AXIS. Use a trusted, updated device and a private network if possible.
2. Do not approve a passkey prompt you did not initiate. Do not share a password, one-time code, CNIC, date of birth, or recovery details with someone who contacts you unexpectedly.
3. Write down what happened and when: account name, last known legitimate sign-in, device lost, suspicious screen, and any affected students, payments, or classes.
4. Tell the school administrator. If the administrator account may be involved, contact the AXIS account/service owner through a known contact method.
5. After access is contained, review the affected account's profile and recent school records. Ask the relevant module owner to check payment receipts, fee logs, attendance audit history, staff status, or class assignments as applicable.

## Staff account may be compromised

### If you can still sign in safely

1. Use a trusted device and the genuine staff portal URL supplied by your school.
2. Open **More** → **Profile** → **Change Password**.
3. Enter the CNIC and date of birth that match your staff profile, then enter and confirm a new, unique password. The staff self-service form requires at least 8 characters, one uppercase letter, one digit, and one symbol; use a longer unique password where possible.
4. Submit the change. AXIS signs this staff account out of all devices. Sign in again with the new password.
5. Immediately tell the school administrator what happened. Ask them to use **Force Logout** on your staff profile and review your account status and recent activity.
6. If you suspect the passkey itself or its syncing account is exposed, ask the administrator to turn off biometric enforcement temporarily. From a trusted signed-in device, disable the saved biometric credential, then register a new passkey only on a device you control.

### If you cannot sign in, or the device was lost

1. Contact the school administrator using a known phone number or in person. Do not use a link or contact number from a suspicious message.
2. Ask the administrator to open **Staff Management** → your staff profile and choose **Force Logout**.
3. Ask the administrator to reset your staff password and, if needed, set your account inactive until you can confirm ownership.
4. If biometric access is required, ask the administrator to turn off the account's biometric-login requirement temporarily so you can use username and password on a clean device.
5. After you regain access, open Profile, disable the old biometric credential, register a new passkey on your trusted device, and ask the administrator to turn biometric enforcement back on if your school requires it.
6. Review assigned classes and notify the administrator of any marks or student changes you do not recognize.

!!! warning "Administrator password reset rules"
    The staff administrator reset form requires a password of at least 12 characters, an uppercase letter, a digit, and a symbol from `!@#$%^&*`. A reset signs the staff member out of all devices. The temporary biometric bypass should be turned back on after the trusted passkey is registered, if that is the school's policy.

## Biometric is enabled, but you are signing in on another device

A passkey is normally available on the device where it was created. It may also sync when the same Apple, Google, or Microsoft account and passkey service are used on both devices.

### The new device has the same synced passkey

1. Open the exact same secure HTTPS staff portal address. Passkeys are tied to the site's origin; a different hostname or non-secure URL will not work.
2. Make sure the browser/device is signed in to the same passkey-sync account used when the passkey was registered.
3. Enter the staff username and password.
4. When the browser asks, choose the AXIS passkey and approve with the device screen lock, fingerprint, or face verification.

### The passkey is not available on the new device

1. Do not keep retrying an unrelated device or different website address. Use the original registered device if it is available and trusted.
2. Contact the school administrator and ask them to temporarily disable biometric login for your staff profile.
3. Sign in on the new trusted device with your username and password.
4. If an old device may be lost or compromised, use **Disable Biometric** from Profile to disable the saved credential. This signs you out; sign in again with the password while biometric enforcement remains off.
5. Open Profile, choose **Enable Biometric**, and register a new passkey on the new device.
6. Test a sign-out/sign-in on the new device. Then ask the administrator to turn biometric enforcement back on.

If the administrator cannot disable the biometric requirement, cannot verify your staff account, or the old passkey may be compromised, ask them to contact the AXIS service owner. Do not try to bypass the login page.

## School administrator account may be compromised

School administrators use the school's administrator username/password, not the staff portal account.

### If you can still sign in from a trusted device

1. Open **Settings**.
2. Change the administrator username if it may be known to someone else.
3. Enter a new unique password in **New Password** and **Confirm Password**, then choose **Save All Changes**.
4. Sign out from the current browser using the profile menu, then sign in again with the new credentials.
5. Contact the AXIS account/service owner promptly and report that the administrator account may have been accessed without permission.
6. Ask them to review or expire other administrator sessions. Changing the password in Settings does not provide a control to remotely revoke every already-open school-admin browser session.
7. Review staff accounts, fee receipts/logs, student records, attendance audit, leave approvals, class assignments, and timetable changes from the suspected period.

### If you cannot sign in

1. Do not ask a staff member to share their account; staff and school-admin sessions are different.
2. Contact the AXIS account/service owner using a known support channel and request administrator account recovery and active-session containment.
3. Provide the school name, portal link, administrator username, time access was lost, and a safe way to verify your identity. Never send the current or previous password.
4. After recovery, set a new unique password, sign out from trusted browser sessions, and audit changes made during the affected period.

!!! note "No admin passkey control is shown"
    The current school-admin Settings page supports changing the username/password, but it does not show a biometric/passkey setup or a remote sign-out-all-sessions control. The staff portal has separate passkey controls. For a suspected school-admin session compromise, involve the AXIS service owner.

## Lost or shared device

| Account/device situation | Immediate action |
|---|---|
| Staff phone lost, account still active | School admin: **Force Logout**, reset password, and temporarily disable biometric enforcement. Staff: disable the old credential after regaining access, register on a trusted device, then re-enable policy. |
| Shared computer used for staff portal | Sign out, close the browser, and tell the administrator if the password may have been saved or the device was not trusted. Ask for a password reset if uncertain. |
| School-admin laptop lost | Contact the AXIS service owner to contain existing admin sessions; change admin credentials from a trusted device as soon as safely possible. |
| Passkey sync account compromised | Secure the Apple/Google/Microsoft account first using its official recovery process, then ask the school administrator to disable/re-register AXIS biometric access. |

## What to review after securing access

- **Staff:** account active/inactive status, assigned classes/subjects, attendance entries, leave requests, and notifications.
- **Fees:** payment receipts, student balances, fee-generation logs, and any unusual item sales.
- **Attendance:** use the administrator's audit/history views to check who changed marks and when.
- **School setup:** name/logo/admin credentials, staff account creation/reset actions, class/subject assignments, holidays, and timetable/teacher changes.
- **Affected families:** the school administrator should follow the school's privacy and incident-notification rules; AXIS cannot determine legal notification requirements for your school.

!!! tip "Preserve evidence"
    Keep receipt numbers, dates, screenshots of suspicious messages (with passwords hidden), and the names of affected records. Do not post screenshots containing student details or credentials in an open group.

## FAQ

### Will changing a staff password sign out other devices?
Yes. The self-service change and administrator reset invalidate that staff member's tracked sessions. The person must sign in again with the new password.

### Will changing the school-admin password sign out every browser?
The Settings page does not offer a remote session-revocation action for school-admin sessions. Change the credentials, sign out of known browsers, and ask the AXIS service owner to contain other active sessions.

### Can an administrator remotely delete a staff passkey?
The school-admin staff profile can enable or disable the biometric-login requirement. The staff member disables registered credentials from their Profile after signing in. If the staff member cannot safely sign in, first disable enforcement and reset/force logout, then remove/re-register credentials from a trusted device.

### Does disabling biometric enforcement change the password?
No. It changes whether a passkey is required for that staff account. Reset the password separately if it may be known to someone else.

### What if I receive a passkey prompt I did not request?
Cancel it. Do not approve. Change the password from a trusted device if safe, notify the administrator, and ask them to force logout and review the account.

### Who should I contact?
Start with your school's designated AXIS administrator. If the school-admin account, portal recovery, or global session containment is involved, that administrator should contact the AXIS service owner using the school's known support channel.

## Related guides

[Staff portal](staff-portal.md) · [School settings](school-settings.md) · [Classes and staff](classes-and-staff.md) · [Attendance](attendance.md) · [Fees and vouchers](fees.md)
