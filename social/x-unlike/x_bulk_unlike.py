"""
X (Twitter) Bulk-Unlike Helper
================================

Purpose:
    Automates clicking "unlike" (the heart icon) on posts in your OWN X
    "Likes" tab, so you don't have to manually tap through thousands of
    posts one by one.

IMPORTANT — READ BEFORE USING
------------------------------
1. This uses browser automation (Playwright) against the normal X website —
   the same thing you'd do by hand, just scripted. It does NOT use any
   private/internal API, does NOT bypass login, and does NOT touch any
   account but your own.
2. This is against X's Terms of Service (no automated interactions), so
   there is a real risk of a temporary action block, rate-limit lock, or
   account flag if it runs too fast or too long. The defaults below are
   deliberately conservative. Increase speed at your own risk.
3. Unlike Instagram, X's Likes tab has no bulk-select UI and no date
   filter/sort — it's a single reverse-chronological scroll, one heart icon
   at a time. This script clicks them one by one with a delay between each.
4. X changes its site markup periodically, so the selectors in this script
   may need small tweaks if it stops finding buttons. Places you may need
   to adjust are marked with "ADJUST ME".
5. You will log in manually in the visible browser window the first time
   (so your password never touches this script or gets typed by the bot).
   The session is then saved locally to `x_session.json` and reused.
6. X and Google both actively detect automated/embedded browsers (Playwright's
   bundled Chromium trips this) and will block or throttle login. To avoid
   that, this script launches your REAL installed Chrome (via
   channel="chrome") instead of Playwright's bundled Chromium — set
   USE_REAL_CHROME = False below only if you don't have Chrome installed.
   You can also skip the in-script login entirely by exporting cookies from
   your normal everyday browser session and pointing SESSION_FILE at them
   (see "Cookie import" below) — this never runs an automated login flow at
   all, which is the most reliable option if X/Google keep blocking login.

Setup
-----
    pip install playwright --break-system-packages
    playwright install chromium
    (Real Chrome must already be installed separately on your system for
    USE_REAL_CHROME = True to work — Playwright just drives it.)

Cookie import (recommended if login keeps getting blocked)
------------------------------------------------------------
    1. In your normal, everyday browser, log into x.com as usual.
    2. Use a cookie-export extension (e.g. "Get cookies.txt LOCALLY" or
       "EditThisCookie") to export cookies for x.com in Playwright's
       storage_state JSON format (some extensions export this directly;
       others export a Netscape cookies.txt that needs converting).
    3. Save that file as `x_session.json` in this script's folder (same
       name as SESSION_FILE below) BEFORE running the script.
    4. Run the script — it'll detect the existing session file and skip the
       login step entirely, going straight to your Likes tab.
    Note: exported cookies are sensitive (they grant full account access
    while valid) — don't share x_session.json with anyone, and delete it
    when you're done.

Usage
-----
    python3 x_bulk_unlike.py

By default (HEADLESS = False) it runs visibly:
    1. If x_session.json already exists (e.g. from cookie import), the
       script skips straight to your Likes tab.
    2. Otherwise, a real Chrome window opens to X login. Log in yourself
       (handle 2FA etc. manually).
    3. Press Enter in the terminal once you're logged in and see your feed.
    4. The script navigates to your Likes tab and starts unliking, scrolling
       down for more as it goes.

Running headless (no visible window):
    1. First, run it once normally (HEADLESS = False) to log in — this
       saves your session to x_session.json.
    2. Set HEADLESS = True in the CONFIG section.
    3. Run again — no browser window will appear.
    Note: headless mode has no way to ask you for help if something goes
    wrong mid-run (e.g. it gets navigated off the Likes page) — it'll just
    stop and print/screenshot what happened, rather than hang waiting for
    input nobody can give it.

Stopping / resuming
--------------------
    Press Ctrl+C at any time to stop safely. Progress isn't tracked between
    runs (X's Likes list just shrinks as you unlike things), so just re-run
    the script to continue from wherever the list starts now.

A note on pacing
-----------------
    X has historically been quicker than Instagram to rate-limit or
    temporarily lock accounts showing bot-like burst behavior. The defaults
    here are slower and the session length shorter than the Instagram
    script's defaults for that reason. If you have thousands of likes,
    plan on running this across several sessions over a few days rather
    than trying to do it all in one sitting.
"""

import json
import random
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ---------------------------------------------------------------------------
# CONFIG — tune these to control speed / safety
# ---------------------------------------------------------------------------

SESSION_FILE = "x_session.json"

# Use your real, locally-installed Chrome instead of Playwright's bundled
# Chromium. Both X and Google actively detect the bundled Chromium as an
# automation tool and block/throttle login — real Chrome is much less
# likely to get flagged. Requires Chrome to already be installed on this
# machine. If you don't have Chrome, set this to False (login may still get
# blocked in that case — cookie import is the more reliable fallback then).
USE_REAL_CHROME = False

# Folder Playwright will use to persist real-Chrome profile data (separate
# from your everyday Chrome profile, so this won't touch your normal
# browsing history/bookmarks/extensions).
USER_DATA_DIR = "x_chrome_profile"

# Your X username (without the @), e.g. "amerikanfutbol". If set, this
# skips auto-detecting your handle entirely — recommended for headless runs,
# since auto-detection failing would otherwise fall back to a manual input()
# prompt that headless mode has no way to answer. Leave "" to auto-detect
# (fine for non-headless runs, where you can type it in if detection fails).
X_HANDLE = "amerikanfutbol"

# Set to True to run with no visible browser window. Requires x_session.json
# to already exist (i.e. you've logged in at least once with HEADLESS = False,
# or imported cookies — see "Cookie import" above). Strongly recommend also
# setting X_HANDLE above so there's no chance of a blocking input() prompt.
HEADLESS = True

# How many individual unlike actions to perform before stopping this run.
# Kept modest by default — see "A note on pacing" above.
MAX_UNLIKES_PER_RUN = 150

# Random delay range (seconds) between each individual unlike click.
MIN_DELAY_BETWEEN_CLICKS = 1.5
MAX_DELAY_BETWEEN_CLICKS = 4.0

# After this many unlikes, take a longer "break" to look less bot-like.
BREAK_EVERY_N_UNLIKES = 20
BREAK_DURATION_SECONDS = (90, 240)  # random range

# How long to wait for new items to load when scrolling.
SCROLL_WAIT_SECONDS = 2.0

# How many consecutive "nothing new after scrolling" attempts before we
# conclude the Likes list is genuinely exhausted (or stuck) and stop.
MAX_EMPTY_SCROLL_RETRIES = 4

LIKES_URL_FRAGMENT = "/likes"

# X marks the like/unlike heart button with a stable internal identifier
# rather than reliable visible/accessible text, so we target that instead
# of a label. When a post is already liked, this button represents the
# "unlike" action.
# ADJUST ME if X changes this identifier (inspect the heart icon's HTML —
# look for data-testid="unlike" or similar on a post you've liked).
UNLIKE_BUTTON_SELECTOR = '[data-testid="unlike"]'


def human_delay(min_s, max_s):
    time.sleep(random.uniform(min_s, max_s))


def load_session_into_context(context, session_file):
    """launch_persistent_context doesn't accept storage_state directly (that
    param only exists on browser.new_context()), so for the real-Chrome path
    we load a previously-saved storage_state JSON's cookies in manually."""
    try:
        data = json.loads(Path(session_file).read_text())
    except Exception as e:
        print(f"Couldn't read {session_file}: {e}")
        return False

    cookies = data.get("cookies", [])
    if not cookies:
        print(f"{session_file} had no cookies in it.")
        return False

    try:
        context.add_cookies(cookies)
        print(f"Loaded {len(cookies)} cookies from {session_file} into the browser.")
        return True
    except Exception as e:
        print(f"Couldn't load cookies into context: {e}")
        return False


def ensure_on_likes_page(page, profile_url):
    """Try to get back to the Likes tab if we've been navigated away
    (e.g. a click accidentally opened a tweet's detail view)."""
    for _ in range(2):
        if LIKES_URL_FRAGMENT in page.url:
            return True
        try:
            page.goto(profile_url, timeout=20000)
            page.wait_for_load_state("load", timeout=20000)
            human_delay(1.5, 2.5)
        except PlaywrightTimeoutError:
            pass
    return LIKES_URL_FRAGMENT in page.url


def main():
    total_unliked = 0
    give_up = False

    with sync_playwright() as p:
        session_exists = Path(SESSION_FILE).exists()

        if HEADLESS and not session_exists:
            print(f"HEADLESS is True but {SESSION_FILE} doesn't exist yet.")
            print("Run once with HEADLESS = False first to log in and save a session.")
            return

        browser = None  # only set in the non-persistent-context branch

        if USE_REAL_CHROME:
            # launch_persistent_context returns a BrowserContext directly
            # (no separate Browser object) and drives your real installed
            # Chrome via channel="chrome", which is far less likely to be
            # flagged as automation by X/Google than Playwright's bundled
            # Chromium. Note: unlike browser.new_context(), this call does
            # NOT accept a storage_state kwarg, so if we have a saved
            # session we load its cookies in manually right after launch.
            context = p.chromium.launch_persistent_context(
                USER_DATA_DIR,
                channel="chrome",
                headless=HEADLESS,
                viewport={"width": 1280, "height": 900},
            )
            if session_exists:
                load_session_into_context(context, SESSION_FILE)
        else:
            browser = p.chromium.launch(headless=HEADLESS)
            context = browser.new_context(
                storage_state=SESSION_FILE if session_exists else None,
                viewport={"width": 1280, "height": 900},
            )

        page = context.new_page() if not context.pages else context.pages[0]

        if not session_exists:
            print("No saved session found. Opening X login page...")
            page.goto("https://x.com/login", timeout=30000)
            input("Log in manually in the browser window, then press Enter here once "
                  "you're on your home feed... ")
            context.storage_state(path=SESSION_FILE)
            print(f"Session saved to {SESSION_FILE}.")

        # Figure out our own handle so we can build the Likes URL and use it
        # for recovery if we get navigated away.
        print("Navigating to your profile to find your handle...")
        page.goto("https://x.com/home", timeout=30000)
        try:
            page.wait_for_load_state("load", timeout=20000)
        except PlaywrightTimeoutError:
            pass
        human_delay(1.5, 2.5)

        handle = X_HANDLE.strip().lstrip("@") if X_HANDLE else None

        if not handle:
            try:
                # ADJUST ME: clicking the account switcher / profile link in the
                # left nav is one reliable way to surface the handle; there are
                # other ways (e.g. reading it off an existing profile link) if
                # X's layout changes.
                profile_link = page.get_by_test_id("AppTabBar_Profile_Link")
                href = profile_link.get_attribute("href")
                if href:
                    handle = href.strip("/")
            except Exception:
                pass

        if not handle:
            if HEADLESS:
                print("Couldn't auto-detect your handle and HEADLESS is True, so there's "
                      "no way to prompt for it. Set X_HANDLE in the CONFIG section and "
                      "re-run.")
                give_up = True
            else:
                handle = input(
                    "Couldn't auto-detect your handle. Type your X username "
                    "(without @) and press Enter: "
                ).strip().lstrip("@")

        if give_up:
            context.close()
            if browser is not None:
                browser.close()
            return

        likes_url = f"https://x.com/{handle}/likes"
        print(f"Going to Likes tab: {likes_url}")
        page.goto(likes_url, timeout=30000)
        try:
            page.wait_for_load_state("load", timeout=30000)
        except PlaywrightTimeoutError:
            pass
        human_delay(2.0, 3.0)

        if HEADLESS:
            try:
                page.screenshot(path="debug_likes_start.png", full_page=False)
                print("Saved debug_likes_start.png so you can confirm the page looks right.")
            except Exception as e:
                print(f"Couldn't save debug screenshot: {e}")
        else:
            input("Confirm the Likes tab loaded correctly in the browser, then press "
                  "Enter here to start unliking... ")

        empty_scroll_retries = 0

        try:
            while total_unliked < MAX_UNLIKES_PER_RUN and not give_up:
                unlike_buttons = page.locator(UNLIKE_BUTTON_SELECTOR)
                count_visible = unlike_buttons.count()

                if count_visible == 0:
                    empty_scroll_retries += 1
                    print(f"  (No unlike buttons visible, scrolling... "
                          f"retry {empty_scroll_retries}/{MAX_EMPTY_SCROLL_RETRIES})")
                    page.mouse.wheel(0, 2500)
                    human_delay(SCROLL_WAIT_SECONDS, SCROLL_WAIT_SECONDS + 1)
                    if empty_scroll_retries >= MAX_EMPTY_SCROLL_RETRIES:
                        print("Nothing new after several scrolls — either your Likes list "
                              "is empty, or the selector no longer matches X's markup.")
                        try:
                            page.screenshot(path="debug_no_posts_found.png", full_page=False)
                            print("Saved debug_no_posts_found.png for diagnosis.")
                        except Exception as e:
                            print(f"Couldn't save debug screenshot: {e}")

                        # If the selector is stale, dump what's actually on
                        # screen so it's easy to find the right one instead
                        # of guessing blind.
                        try:
                            all_buttons = page.locator('[role="button"], button')
                            n = all_buttons.count()
                            print(f"  Found {n} button-like elements. First 20 testids/labels:")
                            for i in range(min(n, 20)):
                                el = all_buttons.nth(i)
                                testid = el.get_attribute("data-testid")
                                label = el.get_attribute("aria-label")
                                print(f"    [{i}] data-testid={testid!r} aria-label={label!r}")
                        except Exception as e:
                            print(f"  Couldn't dump button info: {e}")
                        break
                    continue

                empty_scroll_retries = 0
                btn = unlike_buttons.first

                try:
                    btn.scroll_into_view_if_needed(timeout=5000)
                    btn.click(timeout=5000)
                except Exception as e:
                    print(f"  Click failed ({e}); scrolling and retrying...")
                    page.mouse.wheel(0, 500)
                    human_delay(1.0, 2.0)
                    continue

                # Sanity check: make sure we didn't get bounced off the Likes
                # tab (e.g. the click opened the tweet detail view instead).
                if LIKES_URL_FRAGMENT not in page.url:
                    print("  (Click seems to have navigated away from Likes — recovering...)")
                    if not ensure_on_likes_page(page, likes_url):
                        if HEADLESS:
                            print("Couldn't recover unattended. Stopping this run.")
                            give_up = True
                            break
                        print("Couldn't recover automatically. Please navigate back to your "
                              "Likes tab manually.")
                        input("Press Enter once you're back on the Likes tab... ")
                    continue

                total_unliked += 1
                print(f"Unliked post {total_unliked}/{MAX_UNLIKES_PER_RUN}")

                if total_unliked % BREAK_EVERY_N_UNLIKES == 0:
                    pause = random.uniform(*BREAK_DURATION_SECONDS)
                    print(f"Taking a {pause:.0f}s break to keep things low-key...")
                    time.sleep(pause)
                else:
                    human_delay(MIN_DELAY_BETWEEN_CLICKS, MAX_DELAY_BETWEEN_CLICKS)

        except KeyboardInterrupt:
            print("\nStopped by user.")

        print(f"\nDone for this run. Total unliked: {total_unliked}")
        context.storage_state(path=SESSION_FILE)  # keep session fresh
        context.close()
        if browser is not None:
            browser.close()


if __name__ == "__main__":
    main()
