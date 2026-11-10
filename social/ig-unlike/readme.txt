Instagram Bulk-Unlike Helper
=============================

Purpose:
    Automates clicking "unlike" on posts in your OWN Instagram "Activity ->
    Interactions -> Likes" page, so you don't have to manually tap through
    thousands of posts.

IMPORTANT — READ BEFORE USING
------------------------------
1. This uses browser automation (Playwright) against the normal Instagram
   website — the same thing you'd do by hand, just scripted. It does NOT use
   any private/internal API, does NOT bypass login, and does NOT touch any
   account but your own.
2. This is against Instagram's Terms of Service (no automated interactions),
   so there is a real risk of a temporary action block or warning if you run
   it too fast or too long. The defaults below are deliberately conservative.
   Increase speed at your own risk.
3. Instagram changes its site markup periodically, so the CSS/text selectors
   in this script may need small tweaks if it stops finding buttons. Places
   you may need to adjust are marked with "ADJUST ME".
4. You will log in manually in the visible browser window the first time
   (so your password never touches this script or gets typed by the bot).
   The session is then saved locally to `ig_session.json` and reused.

Setup
-----
    pip install playwright --break-system-packages
    playwright install chromium

Usage
-----
    python3 instagram_bulk_unlike.py

By default (HEADLESS = False at the top of this file) it runs visibly:
    1. A browser window opens to Instagram login. Log in yourself (handle
       2FA etc. manually).
    2. Press Enter in the terminal once you're logged in and see your feed.
    3. The script navigates to your Activity > Likes page. Set your desired
       date range and sort order (oldest to newest) yourself in the UI,
       since Instagram's filter UI is easiest to drive by hand.
    4. Press Enter again once the filtered/sorted list is showing.
    5. The script scrolls and unlikes posts automatically, with pauses.

Running headless (no visible window, so you can use your computer for
other things while it runs):
    1. First, run it once normally (HEADLESS = False) to log in — this
       saves your session to ig_session.json.
    2. Edit the `apply_date_filter()` function below to set the exact date
       range/year you want for this run (see the comments there — the
       example is already filled in from a real recorded run).
    3. Set HEADLESS = True in the CONFIG section.
    4. Run the script again — no browser window will appear, and it'll run
       start-to-finish unattended, applying the filter itself.
    Note: headless mode has no way to ask you for help if something goes
    wrong mid-run (e.g. it gets lost off the Likes page) — it'll just stop
    and print what happened, rather than hang waiting for input nobody
    can give it.

Stopping / resuming
--------------------
    Press Ctrl+C at any time to stop safely. Progress isn't tracked between
    runs (Instagram's activity list re-shrinks as you unlike things), so
    just re-run the script and re-apply your date filter for the next batch.
