"""
Converts a Cookie-Editor JSON export (for x.com) into the storage_state
JSON format Playwright expects (x_session.json), so x_bulk_unlike.py can
load your session without ever running an automated login.

Usage
-----
    1. In your normal browser, log into x.com.
    2. Install the "Cookie-Editor" extension, open it while on x.com, and
       use Export -> JSON. Save that file as x_cookies_raw.json in this
       same folder.
    3. Run:  python3 convert_cookies.py
    4. This writes x_session.json, which x_bulk_unlike.py will pick up
       automatically on its next run.

Note: x_session.json grants full access to your X account while the
cookies remain valid. Don't share it, and delete it when you're done.
"""

import json
from pathlib import Path

INPUT_FILE = "x_cookies_raw.json"
OUTPUT_FILE = "x_session.json"

SAME_SITE_MAP = {
    "no_restriction": "None",
    "unspecified": "None",
    "lax": "Lax",
    "strict": "Strict",
}


def convert(raw_cookies):
    converted = []
    for c in raw_cookies:
        name = c.get("name")
        value = c.get("value")
        domain = c.get("domain")
        if not name or value is None or not domain:
            continue  # skip anything malformed/incomplete

        same_site_raw = str(c.get("sameSite", "lax")).lower()
        same_site = SAME_SITE_MAP.get(same_site_raw, "Lax")

        # Playwright wants numeric "expires" (unix seconds), or -1 for
        # session cookies. Cookie-Editor uses "expirationDate" (also unix
        # seconds) or omits it for session cookies.
        expires = c.get("expirationDate")
        if expires is None:
            expires = -1

        converted.append({
            "name": name,
            "value": value,
            "domain": domain,
            "path": c.get("path", "/"),
            "expires": expires,
            "httpOnly": bool(c.get("httpOnly", False)),
            "secure": bool(c.get("secure", True)),
            "sameSite": same_site,
        })
    return converted


def main():
    if not Path(INPUT_FILE).exists():
        print(f"Couldn't find {INPUT_FILE}. Export your x.com cookies from "
              f"Cookie-Editor as JSON and save them under that name first.")
        return

    raw = json.loads(Path(INPUT_FILE).read_text())
    if isinstance(raw, dict) and "cookies" in raw:
        raw = raw["cookies"]  # some export formats wrap it in a dict

    if not isinstance(raw, list):
        print(f"Unexpected format in {INPUT_FILE} — expected a list of cookie objects.")
        return

    cookies = convert(raw)
    if not cookies:
        print("No usable cookies found after conversion. Check the export file's format.")
        return

    storage_state = {"cookies": cookies, "origins": []}
    Path(OUTPUT_FILE).write_text(json.dumps(storage_state, indent=2))
    print(f"Wrote {len(cookies)} cookies to {OUTPUT_FILE}.")
    print("You can now run x_bulk_unlike.py — it'll pick this session up automatically.")


if __name__ == "__main__":
    main()
