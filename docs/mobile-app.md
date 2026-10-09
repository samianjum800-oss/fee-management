# Mobile and installed apps

## Overview

AXIS works in a browser on desktop, tablet, and phone. The school administrator portal and staff portal are separate web apps and have separate install controls. Installing an app adds a shortcut and an app-like window; it does not create a new account or remove the need to sign in.

## Open AXIS on a phone

1. Use the school-specific administrator link for school records, fees, reports, and setup.
2. Use the staff portal link for your individual teacher/staff account.
3. Open the link in a current browser and sign in.
4. Use the bottom menu. The school portal offers **Home**, **Students**, **Collect**, **Stock**, and **More** when available. The staff portal offers **Home**, **Attendance**, and **More**.
5. Use the **More** page for tools that do not fit in the bottom navigation.

## Install the school portal

Install the school portal only on a device you trust. Its app name and start page are based on the school portal you opened.

=== "Chrome or Edge"

    1. Open the school's AXIS portal over its secure HTTPS address and sign in.
    2. Choose **Install App** if shown.
    3. Accept the browser installation prompt.
    4. If no prompt appears, open the browser menu and choose **Install app** or **Add to Home screen**.
    5. Open the AXIS icon from your device's app list or home screen and sign in.

=== "Safari on iPhone or iPad"

    1. Open the school's AXIS portal in Safari.
    2. Tap **Share**.
    3. Choose **Add to Home Screen** and confirm.
    4. Open the new AXIS icon and sign in.

=== "Firefox"

    1. Open the AXIS portal in Firefox.
    2. Open the browser menu and choose **Add to Home screen** if offered.
    3. Confirm the shortcut and open it from the home screen.

## Install AXIS Staff

Staff installation uses a different app and a different service worker from the school administrator portal.

1. Open the staff portal in your mobile browser and sign in with your staff credentials.
2. Choose **Install App** if it appears, then accept the browser prompt.
3. If there is no prompt, use the browser's manual install steps above.
4. Open **AXIS Staff** from the home screen and sign in.

See [Staff portal, credentials, and AXIS on your device](staff-portal.md) for passkeys, account setup, and lost-device guidance.

## Install the AXIS Help Center

The Help Center is a public, read-only app at `/help/`, separate from the school administrator portal and AXIS Staff.

1. Open your school's AXIS website over HTTPS and visit `/help/`.
2. Tap the floating **Install AXIS Help** button. If a native browser prompt appears, accept it; if not, the button displays manual steps.
3. On iPhone/iPad Safari, use **Share** → **Add to Home Screen**. In Chrome/Edge, use **Install app** or **Add to Home screen**. In Firefox, use its install option if offered.
4. Open **AXIS Help** from the home screen. The floating button hides when the page is running as an installed app.

The Help Center's service worker is limited to `/help/` and caches only help-site pages and local assets. It does not cache school sessions, fees, student data, staff profiles, or attendance records.

## Prepare AXIS Help for offline reading

Open the Help Center online once after installing so the worker can cache the generated manuals and their local assets. Browsers do not allow a site to silently display the native install prompt; the floating button opens it after a user tap.

1. While online, open `/help/` and navigate through the guides you need.
2. Let the pages finish loading while the service worker installs and stores the site's cache list.
3. Open AXIS Help once with the network turned off to check that the guides you need are available.
4. Reconnect and open the Help Center online after an update to refresh cached content.

The offline cache includes the generated Help Center pages and local assets. It does not include AXIS school records, sign-in pages, payment actions, or staff data.

!!! warning "Keep the two portals separate"
    The school administrator app and AXIS Staff are different sign-in experiences. Do not share an administrator account with staff. Sign out of a shared device after use.

## What works offline

- The Help Center can display its cached manuals offline after a successful online visit and cache setup.
- The staff app provides a cached offline fallback page, but it does not cache staff records or authenticated actions.
- The school portal may reuse some previously opened pages, but editing student records, saving payments, changing attendance, and other updates require a working connection.
- Student entries can be queued for synchronization in supported browsers. Keep the same browser/device available and verify that the entry appears in AXIS before relying on it.

!!! note "Do not use offline mode for financial confirmation"
    A payment is not complete until AXIS has saved it and opened or listed its receipt. Do not hand out a receipt based only on an offline screen.

## Common scenarios

- **Install button is missing:** Use the browser menu's install/add-to-home option. Some browsers show the button only after the site meets their install requirements.
- **The installed app asks you to sign in:** This is expected. Installation does not keep your password or bypass account security.
- **You installed the wrong AXIS icon:** Remove the shortcut and install from the correct school portal or staff portal link.
- **You are using a shared device:** Use a private trusted device when possible, do not save passwords on shared browsers, and sign out when finished.

## FAQ

### Does installing AXIS work without an account?
No. The icon opens the portal; a valid school administrator or staff account is still required.

### Does installing the app install software from an app store?
No. AXIS uses your browser's web-app installation or home-screen shortcut feature.

### Why does the browser say the app cannot be installed?
Installation depends on a supported browser, a secure HTTPS website, and the site's app metadata/assets. Try the manual browser menu option or contact the AXIS provider.

### Can I use the administrator app for teacher work?
The administrator and staff portals have separate accounts and navigation. Use the portal assigned to your role.

### Can I read Help Center guides without internet?
Yes, after opening `/help/` online so the manual pages and assets are cached. Reconnect and open the Help Center online to receive updated manuals.

## Troubleshooting

| Problem | What to do |
|---|---|
| Install action does nothing | Confirm internet access, open the exact secure portal URL, refresh, and try the browser's own install menu. |
| Icon opens the wrong school | Remove the shortcut and install from the correct school's link. |
| App shows an offline screen | Reconnect to the internet and choose Retry. Staff data is not available offline. |
| Student entry is not visible after reconnecting | Open AXIS on the same device/browser and allow synchronization; verify the server record before adding it again. |

## Related guides

[Getting started](getting-started.md) · [Staff portal](staff-portal.md) · [Students](students.md) · [Fees and vouchers](fees.md)
