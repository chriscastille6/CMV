#!/usr/bin/env python3
"""
Semi-automated EBSCO PDF download assistant (human-in-the-loop).

Opens queued articles in Chrome via SeleniumBase, waits for you to authenticate
and download PDFs, then optionally runs ingest_uploaded_pdfs.py.

Requires: pip install seleniumbase  (+ Google Chrome)

This script does NOT store credentials or attempt unattended institutional login.

Usage:
  python3 review/EBSCO/ebsco_download_assistant.py --dry-run --limit 5
  python3 review/EBSCO/ebsco_download_assistant.py --limit 10 --ingest-after-batch
  python3 review/EBSCO/ebsco_download_assistant.py --start-rank 50

See review/EBSCO/EBSCO_DOWNLOAD_AUTOMATION.md for feasibility notes.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path

from ebsco_search_order import QUEUE_FILENAME

ROOT = Path(__file__).resolve().parents[2]
EBSCO_DIR = Path(__file__).resolve().parent
QUEUE_PATH = EBSCO_DIR / QUEUE_FILENAME
MASTER_PATH = ROOT / "review" / "master" / "articles_master.csv"
INCOMING_DIR = EBSCO_DIR / "pdfs" / "incoming"
BROWSER_PROFILE = EBSCO_DIR / ".browser_profile"
INGEST_SCRIPT = EBSCO_DIR / "ingest_uploaded_pdfs.py"

# Heuristic selectors for EBSCO / common publisher download controls (best-effort only).
DOWNLOAD_SELECTORS = (
    'a[title*="PDF" i]',
    'a[aria-label*="PDF" i]',
    'button[title*="PDF" i]',
    'a:contains("Download PDF")',
    'a:contains("PDF")',
    'a[href$=".pdf"]',
)


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build_plink_index(master_rows: list[dict[str, str]]) -> dict[str, str]:
    index: dict[str, str] = {}
    for row in master_rows:
        mid = (row.get("article_id") or "").strip().upper()
        plink = (row.get("ebsco_plink") or "").strip()
        if mid and plink:
            index[mid] = plink
    return index


def article_url(row: dict[str, str], plink_index: dict[str, str]) -> str:
    mid = (row.get("master_article_id") or "").strip().upper()
    plink = plink_index.get(mid, "")
    if plink:
        return plink
    doi = (row.get("doi") or "").strip()
    if doi:
        return f"https://doi.org/{doi.lstrip('https://doi.org/')}"
    return ""


def load_queue(limit: int | None, start_rank: int) -> list[dict[str, str]]:
    rows = load_csv(QUEUE_PATH)
    filtered = []
    for row in rows:
        try:
            rank = int(row.get("queue_rank") or 0)
        except ValueError:
            continue
        if rank < start_rank:
            continue
        filtered.append(row)
    if limit is not None:
        filtered = filtered[:limit]
    return filtered


def run_ingest(incoming_only: bool = False) -> int:
    cmd = [sys.executable, str(INGEST_SCRIPT), "--scan-downloads"]
    if incoming_only:
        # ingest scans ~/Downloads by default; also pick up incoming via --pdf glob below
        pass
    # Scan incoming folder explicitly
    pdfs = sorted(INCOMING_DIR.glob("*.pdf"))
    if not pdfs and not incoming_only:
        print("ingest: no PDFs in incoming/; scanning ~/Downloads via ingest script")
        return subprocess.call(cmd)
    rc = 0
    for pdf in pdfs:
        print(f"ingest: {pdf.name}")
        rc = subprocess.call([sys.executable, str(INGEST_SCRIPT), "--pdf", str(pdf)]) or rc
    if not pdfs:
        rc = subprocess.call(cmd)
    return rc


def try_download_click(sb) -> bool:
    """Best-effort click on a PDF download control; returns True if clicked."""
    for selector in DOWNLOAD_SELECTORS:
        try:
            if sb.is_element_visible(selector):
                sb.click(selector)
                return True
        except Exception:
            continue
    return False


def interactive_loop(args: argparse.Namespace) -> int:
    try:
        from seleniumbase import SB
    except ImportError:
        print(
            "seleniumbase not installed. Run: pip install seleniumbase",
            file=sys.stderr,
        )
        return 1

    master_rows = load_csv(MASTER_PATH)
    plink_index = build_plink_index(master_rows)
    queue = load_queue(args.limit, args.start_rank)
    if not queue:
        print("No queue rows to process.")
        return 0

    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    BROWSER_PROFILE.mkdir(parents=True, exist_ok=True)
    profile = Path(args.user_data_dir) if args.user_data_dir else BROWSER_PROFILE

    print(f"Queue: {len(queue)} articles (from rank {args.start_rank})")
    print(f"Download folder: {INCOMING_DIR}")
    print(f"Browser profile: {profile}")
    print()

    sb_kwargs = dict(
        browser=args.browser,
        headed=True,
        uc=args.uc_mode,
        user_data_dir=str(profile),
        download_folder=str(INCOMING_DIR),
    )

    processed = 0
    skipped = 0

    with SB(**sb_kwargs) as sb:
        sb.set_window_size(1400, 900)
        sb.open("https://research.ebsco.com/")
        print(
            "\n>>> Log in to your institution in the browser window if needed.\n"
            ">>> When ready, return here and press Enter to start the queue.\n"
        )
        input()

        for row in queue:
            rank = row.get("queue_rank", "?")
            mid = row.get("master_article_id", "")
            title = (row.get("title") or "")[:80]
            url = article_url(row, plink_index)

            if not url:
                print(f"[{rank}] SKIP {mid} — no ebsco_plink or DOI")
                skipped += 1
                continue

            print(f"\n[{rank}] {mid}: {title}")
            print(f"  → {url}")

            before = {p.name for p in INCOMING_DIR.glob("*.pdf")}
            sb.open(url)
            time.sleep(args.page_wait)

            if args.auto_click:
                clicked = try_download_click(sb)
                if clicked:
                    print("  (auto-click attempted; waiting for download…)")
                    time.sleep(args.download_wait)
                else:
                    print("  (no auto-click match — download manually in browser)")

            if args.interactive:
                print(
                    "  Download the PDF, then press Enter for next article "
                    "(or type 's' to skip, 'q' to quit): "
                )
                choice = input().strip().lower()
                if choice == "q":
                    break
                if choice == "s":
                    skipped += 1
                    continue
            else:
                time.sleep(args.download_wait)

            after = {p.name for p in INCOMING_DIR.glob("*.pdf")}
            new_files = after - before
            if new_files:
                print(f"  ✓ detected: {', '.join(sorted(new_files))}")
            else:
                print("  ? no new PDF in incoming/ (may be in ~/Downloads)")

            processed += 1

    print(f"\nDone. processed={processed} skipped={skipped}")

    if args.ingest_after_batch and processed:
        print("\nRunning ingest…")
        return run_ingest()

    return 0


def dry_run(args: argparse.Namespace) -> int:
    master_rows = load_csv(MASTER_PATH)
    plink_index = build_plink_index(master_rows)
    queue = load_queue(args.limit, args.start_rank)
    print(f"Dry run — {len(queue)} articles\n")
    for row in queue:
        url = article_url(row, plink_index)
        print(
            f"{row.get('queue_rank'):>4}  {row.get('master_article_id'):<6}  "
            f"{url or '(no url)'}"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print URLs only")
    parser.add_argument("--limit", type=int, default=None, help="Max articles this run")
    parser.add_argument(
        "--start-rank",
        type=int,
        default=1,
        help="First queue_rank to process (default: 1)",
    )
    parser.add_argument(
        "--browser",
        default="chrome",
        choices=["chrome", "edge"],
        help="Browser (default: chrome)",
    )
    parser.add_argument(
        "--user-data-dir",
        default="",
        help=f"Chrome profile dir (default: {BROWSER_PROFILE})",
    )
    parser.add_argument(
        "--uc-mode",
        action="store_true",
        help="Enable SeleniumBase UC mode (undetected chromedriver)",
    )
    parser.add_argument(
        "--auto-click",
        action="store_true",
        help="Try heuristic PDF download clicks (fragile)",
    )
    parser.add_argument(
        "--no-interactive",
        dest="interactive",
        action="store_false",
        help="Do not pause between articles",
    )
    parser.set_defaults(interactive=True)
    parser.add_argument(
        "--page-wait",
        type=float,
        default=3.0,
        help="Seconds after opening each URL",
    )
    parser.add_argument(
        "--download-wait",
        type=float,
        default=8.0,
        help="Seconds to wait for download",
    )
    parser.add_argument(
        "--ingest-after-batch",
        action="store_true",
        help="Run ingest_uploaded_pdfs.py after the session",
    )
    args = parser.parse_args()

    if args.dry_run:
        return dry_run(args)
    return interactive_loop(args)


if __name__ == "__main__":
    raise SystemExit(main())
