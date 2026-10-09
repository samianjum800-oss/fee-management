# Staff portal, credentials, and AXIS on your device

## Overview

The AXIS Staff Portal is a separate sign-in for teachers and school staff. It provides a staff dashboard, assigned classes and students, student attendance, leave requests, notifications, profile/password controls, and optional biometric sign-in. The pages and actions available depend on your role and what the school has enabled.

## Sign in

1. Ask your school administrator for the **staff portal link**, username, and first password.
2. Open the staff link. It normally ends in `/portal/staff/login/` and does not include your school's name in the address.
3. Enter your staff username and password.
4. If AXIS asks you to set up a passkey, continue to **Set up biometric access** below. If a passkey is already registered and required, approve the device prompt.
5. After sign-in, open **Home**, **Attendance**, or **More** from the bottom menu.

The staff username is separate from the school administrator username. Staff accounts are created and managed by the school administrator.

## What staff can see

- **Home:** assigned classes, student counts, today's attendance summary, and recent notices.
- **Attendance:** full-day registers for classes where you are class teacher and assigned subject periods for today. Past-day access follows administrator rules.
- **More → Classes:** classes linked to you as class teacher or subject teacher, and the permitted student roster/profile.
- **More → Leave:** policy, remaining quota, leave application, and request history when enabled.
- **More → Notifications:** notices sent to the staff portal.
- **More → Profile:** your staff details, biometric status, and password-change controls.

```text
Bottom menu:  [Home]          [Attendance]          [More]
More:         Classes | Leave | Notifications | Profile | Logout
```

## Set up biometric access (passkey)

AXIS uses your device's passkey capability. Your device may ask for a fingerprint, Face ID, or screen lock. AXIS receives a secure passkey response; it does not receive your fingerprint or face image.

1. Open **Profile** or follow the setup screen after signing in.
2. Review the consent message. Do not register a passkey on a shared device.
3. Choose **Enable Biometric** and then **I Agree & Enable**.
4. When your device prompts, use its fingerprint, face, or screen-lock verification and complete the browser confirmation.
5. Return to the profile and verify that biometric access shows as enabled.
6. On a future sign-in, enter your staff username and password and approve the passkey prompt.

Biometric sign-in needs a secure HTTPS website and a browser/device that supports passkeys. If your administrator has disabled biometric login for your account, AXIS will not require setup.

!!! warning "Use a device you control"
    A passkey may be available to other devices signed in to the same Apple, Google, or Microsoft account when that account syncs passkeys. Never register on a public/shared computer. If a device is lost, tell your administrator so they can disable biometric login and reset your password.

## Change your staff password

1. Open **More** → **Profile** and find **Change Password**.
2. Enter the CNIC and date of birth already saved in your staff record when the form requests identity verification.
3. Enter the new password twice. It must be at least 8 characters and contain an uppercase letter, a digit, and a symbol.
4. Submit the change. AXIS signs your account out of all devices; sign in again with the new password.

If your CNIC or date of birth does not match your staff record, ask the school administrator to correct the staff profile or reset your account. Do not send those identity details in a public channel.

## Install AXIS Staff on your device

Use a secure website address and sign in before installing. The **Install App** control appears in the signed-in staff portal when the browser allows installation.

=== "Chrome or Edge"

    1. Open the staff portal in Chrome or Edge and sign in.
    2. Choose **Install App** if it appears.
    3. Accept the browser's install prompt. If no prompt appears, open the browser menu and choose **Install app** or **Add to Home screen**.
    4. Launch **AXIS Staff** from your device's app list or home screen.

=== "Safari on iPhone or iPad"

    1. Open the staff portal in Safari and sign in.
    2. Tap **Share**.
    3. Choose **Add to Home Screen**, then confirm.
    4. Open the AXIS Staff icon from your home screen.

=== "Firefox"

    1. Open the staff portal in Firefox and sign in.
    2. Use the browser menu and choose **Install** or **Add to Home screen** if offered.
    3. Follow the browser confirmation.

!!! note "Offline use is limited"
    The staff app can show a branded offline page, but it does not store authenticated class, student, attendance, or notification data for offline viewing. Reconnect to use staff features.

## Desktop and mobile

=== "Phone"

    The staff portal is designed around the bottom navigation. Use **More** for classes, leave, notifications, and profile. Keep your device screen lock enabled when using passkeys.

=== "Desktop or tablet"

    Sign in through the same staff URL. Browser passkeys may use a security key, computer screen lock, or a passkey synced from your account. Attendance and class pages remain available, though the staff layout is mobile-focused.

## Notifications

Open **More** → **Notifications** to review staff notices. Open the notice or mark it read from the notification screen. If a notice relates to attendance or leave, follow its link and verify the class/date before taking action. Notifications are in-portal messages; they are not a replacement for school emergency communication.

## Common scenarios

- **First sign-in:** Use the administrator-provided account, complete any requested passkey setup, and check that your name and role are correct in Profile.
- **New phone:** Use the [new-device passkey steps](account-security.md#biometric-is-enabled-but-you-are-signing-in-on-another-device). If the passkey is not synced, ask the administrator to temporarily disable biometric enforcement while you register the new device.
- **Forgotten password:** Contact the school administrator for a reset. A reset signs out all active devices.
- **You cannot see a class:** Ask the administrator to check that you are active and assigned as class teacher or subject teacher.
- **Device lost:** Tell the administrator immediately, ask them to disable biometric access if needed, and reset your staff password.

## FAQ

### Is my staff username the same as my school-admin login?
No. Staff accounts are separate and are created by the school administrator.

### Does AXIS store my fingerprint or face scan?
No. The device verifies you locally and provides a signed passkey response. AXIS stores the credential information needed to verify the passkey, not the biometric image.

### Why does login ask for a passkey after I enter the password?
A passkey is registered and biometric login is enabled for your staff account. Approve the prompt on a device that has the passkey.

### Can I use the installed app without internet?
Only the offline fallback page is guaranteed to be available. Staff data and actions need a connection.

### Why was I signed out on every device after changing my password?
AXIS ends all active sessions for that staff member after a password change or administrator reset. Sign in again with the new password.

## Troubleshooting

| Problem | What to do |
|---|---|
| Username/password rejected | Check the staff username (not the admin login), confirm the account is active, and ask the administrator to reset the password if needed. |
| Too many login attempts | Wait for the temporary block to expire, then ask the administrator to verify the account if it continues. |
| Passkey prompt is cancelled or not found | Try the device/account where the passkey was registered. If the device was replaced, contact the administrator. |
| Biometric setup fails | Open the exact secure HTTPS staff URL in a supported browser, enable the device screen lock, and retry. |
| Install App is missing | Use the browser's manual install menu. Installation availability depends on browser, HTTPS, and device support. |
| A page says feature unavailable | Ask the administrator to confirm your school has enabled that staff feature. |

## Related guides

[Classes and staff](classes-and-staff.md) · [Attendance](attendance.md) · [Leave management](leave.md) · [Mobile and installed apps](mobile-app.md) · [Account security](account-security.md) · [Getting started](getting-started.md)
