import random
import re
import time
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ---------------------------------------------------------------------------
# CONFIG — tune these to control speed / safety
# ---------------------------------------------------------------------------

SESSION_FILE = "ig_session.json"

# Set to True to run with no visible browser window at all, so you can use
# your computer for other things while this runs. Requirements for headless:
#   1. ig_session.json must already exist (i.e. you've logged in at least
#      once with HEADLESS = False).
#   2. You must fill in APPLY_DATE_FILTER below to match the exact filter
#      you want, since there's no visible window to set it by hand.
# If either of those isn't true yet, leave this False.
HEADLESS = True

# How many BULK-UNLIKE actions (batches) to perform before stopping this run.
# Each batch selects up to BATCH_SIZE posts and unlikes them in one action.
MAX_BATCHES_PER_RUN = 20

# Posts selected per batch before clicking the bulk "Unlike" button.
# Instagram's own UI caps selection at 100.
BATCH_SIZE = 100

# Random delay range (seconds) between each individual thumbnail selection click.
MIN_DELAY_BETWEEN_CLICKS = 0.4
MAX_DELAY_BETWEEN_CLICKS = 1.2

# Delay after clicking the bulk "Unlike" button, before starting the next batch.
MIN_DELAY_BETWEEN_BATCHES = 5.0
MAX_DELAY_BETWEEN_BATCHES = 12.0

# After this many batches, take a longer "break" to look less bot-like.
BREAK_EVERY_N_BATCHES = 5
BREAK_DURATION_SECONDS = (60, 180)  # random range

# How long to wait for new items to load when scrolling.
SCROLL_WAIT_SECONDS = 2.0

# Instagram's Likes selection UI renders a dedicated "Toggle checkbox" button
# per post, separate from the thumbnail itself. We click these instead of the
# thumbnail/photo button, since clicking the actual photo/video sometimes
# opens it (navigates away, or triggers video fullscreen) instead of just
# selecting it.
TOGGLE_CHECKBOX_NAME = "Toggle checkbox"


def apply_date_filter(page):
    """
    Scripts the "Sort & filter" flow so the whole run can go headless with
    no visual confirmation step. This is built from the exact steps
    `playwright codegen` recorded on this account — if Instagram's filter UI
    changes, re-run `playwright codegen` on the Likes page yourself and
    update the lines below to match.

    EDIT THIS before running headless: set the year (or whatever combobox
    values represent your desired date range) for the batch you want to run.
    """
    page.get_by_role("button", name="Sort & filter").click()
    human_delay(0.3, 0.6)
    page.get_by_role("button", name="Oldest to newest").click()
    human_delay(0.3, 0.6)

    # ADJUST ME: this was the exact call captured via codegen for filtering
    # to a specific year. The index (5) and available values depend on
    # Instagram's current filter UI — re-run codegen to confirm if unsure.
    # Example: page.get_by_role("combobox").nth(5).select_option("2017")
    page.get_by_role("combobox").nth(5).select_option("2022")
    human_delay(0.3, 0.6)

    page.get_by_role("button", name="Apply").click()

    # Applying the filter likely triggers a full reload — wait for it to
    # actually settle before the caller starts looking for posts.
    try:
        page.wait_for_load_state("load", timeout=90000)
    except PlaywrightTimeoutError:
        pass
    try:
        page.wait_for_load_state("networkidle", timeout=40000)
    except PlaywrightTimeoutError:
        pass
    human_delay(1.0, 2.0)

    # Since there's no visible window in headless mode, save a screenshot
    # so you can check what the page actually looks like if something's off.
    try:
        page.screenshot(path="debug_after_filter.png", full_page=False)
        print("Saved a screenshot of the post-filter page to debug_after_filter.png")
    except Exception as e:
        print(f"Couldn't save debug screenshot: {e}")

    print(f"  Page title: {page.title()!r}")
    print(f"  Page URL: {page.url}")


def exit_fullscreen_if_needed(page):
    """
    Detects if a click accidentally triggered a video's native fullscreen
    playback (this doesn't always change the URL, so the ensure_on_likes_page
    check alone won't catch it) and exits it via Escape, which is how
    browsers exit the Fullscreen API regardless of what the page's own JS
    does.
    """
    try:
        is_fs = page.evaluate("() => !!document.fullscreenElement")
    except Exception:
        is_fs = False
    if is_fs:
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        time.sleep(0.7)
    return is_fs


def human_delay(a, b):
    time.sleep(random.uniform(a, b))


LIKES_URL_FRAGMENT = "your_activity/interactions/likes"


def ensure_on_likes_page(page, max_attempts=3):
    """
    Detects if a click accidentally navigated away from the Likes page
    (e.g. opened a post's lightbox/fullscreen view instead of toggling its
    selection checkbox) and tries to recover by pressing Escape and/or
    going back in browser history.

    Returns True if we're back on the Likes page, False if recovery failed
    (in which case the caller should ask the user to step in manually).
    """
    for _ in range(max_attempts):
        exit_fullscreen_if_needed(page)
        if LIKES_URL_FRAGMENT in page.url:
            return True
        # Close any open lightbox/modal/fullscreen video first.
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        time.sleep(0.5)
        if LIKES_URL_FRAGMENT in page.url:
            return True
        try:
            page.go_back(timeout=5000)
        except Exception:
            pass
        time.sleep(1.5)
    return LIKES_URL_FRAGMENT in page.url


def main():
    with sync_playwright() as p:
        session_path = Path(SESSION_FILE)

        if HEADLESS and not session_path.exists():
            print("HEADLESS is True but no saved session was found.")
            print(f"Run once with HEADLESS = False first to log in and create {SESSION_FILE}.")
            sys.exit(1)

        # --disable-gpu can help on old/flaky GPU drivers (e.g. old MacBooks on
        # newer macOS versions) where hardware-accelerated rendering is slower
        # or less stable than software rendering.
        browser = p.chromium.launch(headless=HEADLESS, args=["--disable-gpu"])

        if session_path.exists():
            context = browser.new_context(storage_state=str(session_path))
        else:
            context = browser.new_context()

        page = context.new_page()
        page.goto("https://www.instagram.com/")

        if not session_path.exists():
            print("Please log in manually in the opened browser window.")
            input("Press Enter here once you're logged in and see your feed... ")
            context.storage_state(path=SESSION_FILE)
            print(f"Session saved to {SESSION_FILE} for next time.")

        # Navigate to Activity -> Interactions -> Likes.
        # ADJUST ME: Instagram sometimes moves this under Settings > Your Activity,
        # or Accounts Center. If this direct URL 404s, navigate there manually.
        try:
            page.goto("https://www.instagram.com/your_activity/interactions/likes/", timeout=15000)
        except PlaywrightTimeoutError:
            print("Couldn't auto-navigate to the Likes activity page.")
            print("Please navigate there manually in the browser window.")

        if HEADLESS:
            print("Applying date filter and sort order automatically (headless mode)...")
            apply_date_filter(page)
        else:
            print("\nNow, in the browser:")
            print("  1. Set your date range filter (start/end date).")
            print("  2. Set sort order to oldest -> newest.")
            print("  3. Make sure the filtered list of liked posts is visible.")
            print("     (Do NOT click 'Select' yourself — the script does that.)")
            input("Press Enter here once that's all set up... ")

        total_unliked = 0
        batches_done = 0
        give_up = False

        print("Starting bulk-unlike loop. Press Ctrl+C to stop at any time.\n")

        try:
            while batches_done < MAX_BATCHES_PER_RUN:
                # --- Recover first, in case a previous click left us off the Likes page ---
                if not ensure_on_likes_page(page):
                    if HEADLESS:
                        print("Lost track of the Likes page and can't recover unattended. "
                              "Stopping this run — check the account manually.")
                        break
                    print("Not on the Likes page and couldn't recover automatically.")
                    input("Please navigate back to the filtered Likes list manually, "
                          "then press Enter to continue... ")

                # --- Enter selection mode ---
                # ADJUST ME: if Instagram's UI changes, this text/role may need updating.
                # Use a generous timeout here since the page may still be settling
                # after the previous batch's full reload.
                try:
                    page.get_by_text("Select", exact=True).click(timeout=40000)
                except PlaywrightTimeoutError:
                    print("Couldn't find 'Select' the first time — the bulk-unlike reload may "
                          "have reset the sort/filter. Reapplying it and retrying...")
                    try:
                        page.screenshot(path="debug_select_missing.png", full_page=False)
                        print(f"  Saved debug_select_missing.png. "
                              f"Page title: {page.title()!r}, URL: {page.url}")
                    except Exception:
                        pass

                    if HEADLESS:
                        try:
                            apply_date_filter(page)
                        except Exception as e:
                            print(f"  Reapplying the filter failed: {e}")

                    try:
                        page.get_by_text("Select", exact=True).click(timeout=40000)
                    except PlaywrightTimeoutError:
                        if HEADLESS:
                            print("Still couldn't find 'Select' after reapplying the filter. "
                                  "Stopping this run unattended — check debug_select_missing.png.")
                            give_up = True
                        else:
                            print("Still couldn't find 'Select'. The page may need a manual nudge.")
                            input("Please check the browser, fix the view if needed, "
                                  "then press Enter to continue (or Ctrl+C to stop)... ")

                if give_up:
                    break

                human_delay(0.5, 1.0)

                # --- Select up to BATCH_SIZE not-yet-selected posts, via their
                # dedicated "Toggle checkbox" buttons (not the thumbnail itself). ---
                selected_count = 0

                while selected_count < BATCH_SIZE and not give_up:
                    checkboxes = page.get_by_role("button", name=TOGGLE_CHECKBOX_NAME)
                    count_visible = checkboxes.count()

                    if count_visible == 0:
                        # Retry a few times with waits — the page may just be slow
                        # to lazy-load, especially right after entering selection
                        # mode or scrolling into fresh territory. Also check for
                        # (and exit) accidental video fullscreen, which hides the
                        # grid without necessarily changing the URL.
                        for retry in range(4):
                            if exit_fullscreen_if_needed(page):
                                print("  (Exited an accidental fullscreen video.)")
                            page.mouse.wheel(0, 2000)
                            human_delay(SCROLL_WAIT_SECONDS, SCROLL_WAIT_SECONDS + 1)
                            checkboxes = page.get_by_role("button", name=TOGGLE_CHECKBOX_NAME)
                            count_visible = checkboxes.count()
                            if count_visible > 0:
                                break
                            print(f"  (No posts visible yet, retry {retry + 1}/4...)")
                        if count_visible == 0:
                            break  # genuinely nothing left to load

                    clicked_something_new = False
                    for i in range(count_visible):
                        if selected_count >= BATCH_SIZE:
                            break
                        cb = checkboxes.nth(i)

                        # Prefer our own marker (set right after a successful click,
                        # see below) since we can't be sure Instagram exposes
                        # aria-pressed/aria-checked reliably on this element. Fall
                        # back to those attributes too, in case it does.
                        already_marked = cb.get_attribute("data-igscript-selected")
                        state = cb.get_attribute("aria-pressed") or cb.get_attribute("aria-checked")
                        if already_marked == "1" or state == "true":
                            continue

                        try:
                            cb.click(timeout=3000)
                            cb.evaluate("el => el.setAttribute('data-igscript-selected', '1')")
                        except Exception:
                            continue

                        # Check for accidental video fullscreen first — this can
                        # happen without the URL changing at all.
                        if exit_fullscreen_if_needed(page):
                            print("  (Click triggered fullscreen video — exited, retrying.)")
                            break

                        # Detect if that click accidentally opened the post itself
                        # (lightbox/fullscreen) instead of toggling its checkbox.
                        if LIKES_URL_FRAGMENT not in page.url:
                            print("  (Click opened a post instead of selecting it — recovering...)")
                            if not ensure_on_likes_page(page):
                                if HEADLESS:
                                    print("Couldn't recover unattended. Stopping this run.")
                                    give_up = True
                                    break
                                print("Couldn't recover back to the Likes page automatically. "
                                      "Please navigate back manually.")
                                input("Press Enter once you're back on the filtered Likes list... ")
                            # Re-enter selection mode since navigating away likely exited it.
                            try:
                                page.get_by_text("Select", exact=True).click(timeout=5000)
                            except PlaywrightTimeoutError:
                                pass
                            # Don't count this as a successful selection; refresh button list and retry.
                            break

                        selected_count += 1
                        clicked_something_new = True
                        human_delay(MIN_DELAY_BETWEEN_CLICKS, MAX_DELAY_BETWEEN_CLICKS)

                    if not clicked_something_new:
                        # Nothing new found on screen; try scrolling for more.
                        page.mouse.wheel(0, 2000)
                        human_delay(SCROLL_WAIT_SECONDS, SCROLL_WAIT_SECONDS + 1)
                        new_count = page.get_by_role("button", name=TOGGLE_CHECKBOX_NAME).count()
                        if new_count <= count_visible:
                            break  # scrolling isn't revealing anything new; stop this batch

                if give_up:
                    break

                if selected_count == 0:
                    print("No liked posts found in view after several retries — "
                          "either this date range is fully cleared, or the page needs "
                          "a manual nudge (try scrolling/reloading and re-running).")
                    try:
                        page.screenshot(path="debug_no_posts_found.png", full_page=False)
                        print("Saved a screenshot to debug_no_posts_found.png for diagnosis.")
                        print(f"  Page title: {page.title()!r}")
                        print(f"  Page URL: {page.url}")
                    except Exception as e:
                        print(f"Couldn't save debug screenshot: {e}")

                    # Dump the actual accessible names of buttons on screen, since
                    # our regex clearly isn't matching whatever's really there.
                    try:
                        all_buttons = page.get_by_role("button")
                        n = all_buttons.count()
                        print(f"  Found {n} <button role> elements total. First 20 names:")
                        for i in range(min(n, 20)):
                            try:
                                name = all_buttons.nth(i).get_attribute("aria-label")
                            except Exception:
                                name = "<error reading aria-label>"
                            print(f"    [{i}] {name!r}")
                    except Exception as e:
                        print(f"  Couldn't dump button names: {e}")
                    break

                print(f"Selected {selected_count} posts for this batch.")

                # --- Click the bulk Unlike button ---
                # NOTE: Instagram's UI sometimes renders more than one element matching
                # this role/name (e.g. duplicate nodes for transition animations), so we
                # don't use exact=True / strict matching here — just click the first
                # visible match.
                unlike_buttons = page.get_by_role("button", name="Unlike")
                clicked_unlike = False
                try:
                    unlike_count = unlike_buttons.count()
                    for i in range(unlike_count):
                        candidate = unlike_buttons.nth(i)
                        if candidate.is_visible():
                            candidate.click(timeout=5000)
                            clicked_unlike = True
                            break
                except Exception as e:
                    print(f"Error while trying to click 'Unlike': {e}")

                if not clicked_unlike:
                    print("Couldn't find a visible bulk 'Unlike' button after selecting posts. "
                          "Check the browser window — the UI may need manual confirmation.")
                    break

                # Instagram may show a confirmation dialog — handle it if present.
                try:
                    page.get_by_role("button", name=re.compile("^Unlike$")).click(timeout=3000)
                except PlaywrightTimeoutError:
                    pass  # no confirmation dialog appeared, that's fine

                batches_done += 1
                total_unliked += selected_count
                print(f"Batch {batches_done} done. Total unliked so far: {total_unliked}")

                # The bulk unlike triggers a full page reload (not just a DOM update),
                # which can take a while. Wait for it to actually settle instead of
                # guessing with a fixed delay, or the next batch's clicks will fire
                # too early and fail/timeout.
                print("Waiting for the page to reload after this batch...")
                try:
                    page.wait_for_load_state("load", timeout=90000)
                except PlaywrightTimeoutError:
                    print("  (Reload took longer than expected — continuing anyway.)")
                try:
                    page.wait_for_load_state("networkidle", timeout=40000)
                except PlaywrightTimeoutError:
                    pass  # not critical if network never fully idles

                # IMPORTANT: the sort order / date filter isn't reflected in the URL,
                # so a full page reload (which the bulk unlike triggers) likely resets
                # it back to Instagram's default (newest-first, unfiltered) view. If
                # we don't reapply it here, the next batch could silently select and
                # unlike posts from the WRONG date range. Reapply every time in
                # headless mode, since there's no one watching to catch this visually.
                if HEADLESS:
                    print("Reapplying date filter/sort before the next batch...")
                    try:
                        apply_date_filter(page)
                    except Exception as e:
                        print(f"  Couldn't reapply filter: {e}. Next batch may be on the wrong range.")

                if batches_done % BREAK_EVERY_N_BATCHES == 0:
                    pause = random.uniform(*BREAK_DURATION_SECONDS)
                    print(f"Taking a {pause:.0f}s break to keep things low-key...")
                    time.sleep(pause)
                else:
                    human_delay(MIN_DELAY_BETWEEN_BATCHES, MAX_DELAY_BETWEEN_BATCHES)

        except KeyboardInterrupt:
            print("\nStopped by user.")

        print(f"\nDone for this run. Batches: {batches_done}, total unliked: {total_unliked}")
        context.storage_state(path=SESSION_FILE)  # keep session fresh
        browser.close()


if __name__ == "__main__":
    main()
