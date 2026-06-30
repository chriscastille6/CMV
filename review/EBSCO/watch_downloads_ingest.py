#!/usr/bin/env python3
"""
Safari-friendly EBSCO download batch assistant (human-in-the-loop).

Uses your existing Safari institutional login — no Chrome profile or Selenium.
Opens queued ebsco_plink URLs in Safari, watches ~/Downloads for new PDFs,
and auto-ingests via ingest_uploaded_pdfs.py.

Requires: macOS (uses `open -a Safari`). Safari must already be logged in to EBSCO.

Usage:
  # Next 10 articles from queue rank 1 (opens one URL at a time)
  python3 review/EBSCO/watch_downloads_ingest.py --limit 10

  # Resume at rank 81
  python3 review/EBSCO/watch_downloads_ingest.py --start-rank 81 --limit 10

  # Print URLs only — no browser, no watch
  python3 review/EBSCO/watch_downloads_ingest.py --dry-run --limit 5

  # Open all URLs in Safari tabs, then watch Downloads until batch done
  python3 review/EBSCO/watch_downloads_ingest.py --limit 10 --open-all-tabs

See review/EBSCO/EBSCO_DOWNLOAD_AUTOMATION.md § Recommended workflow for Safari users.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EBSCO_DIR = Path(__file__).resolve().parent
MASTER_PATH = ROOT / "review" / "master" / "articles_master.csv"
INGEST_SCRIPT = EBSCO_DIR / "ingest_uploaded_pdfs.py"
PROGRESS_SCRIPT = ROOT / "review" / "master" / "progress_counter.py"
DOWNLOADS_DIR = Path.home() / "Downloads"

# Reuse queue / URL helpers from the Selenium assistant.
sys.path.insert(0, str(EBSCO_DIR))
from ebsco_download_assistant import (  # noqa: E402
    article_url,
    build_plink_index,
    load_csv,
    load_queue,
)


def master_has_pdf(master_rows: list[dict[str, str]], article_id: str) -> bool:
    aid = article_id.strip().upper()
    for row in master_rows:
        if (row.get("article_id") or "").strip().upper() != aid:
            continue
        return (row.get("has_pdf") or "").lower() == "true" and bool(
            (row.get("pdf_path") or "").strip()
        )
    return False


def snapshot_pdfs(
    downloads_dir: Path,
    glob_pattern: str,
    min_mtime: float | None = None,
) -> dict[str, float]:
    """Return {filename: mtime} for matching PDFs."""
    out: dict[str, float] = {}
    for path in downloads_dir.glob(glob_pattern):
        if not path.is_file() or path.suffix.lower() != ".pdf":
            continue
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if min_mtime is not None and mtime < min_mtime:
            continue
        out[path.name] = mtime
    return out


def find_new_pdf(
    before: dict[str, float],
    after: dict[str, float],
) -> Path | None:
    """Return path to the newest PDF that appeared since `before`."""
    new_names = set(after) - set(before)
    if not new_names:
        # Same filename overwritten — pick largest mtime increase.
        candidates: list[tuple[float, str]] = []
        for name, mtime in after.items():
            prev = before.get(name)
            if prev is None or mtime > prev + 0.5:
                candidates.append((mtime, name))
        if not candidates:
            return None
        candidates.sort(reverse=True)
        return DOWNLOADS_DIR / candidates[0][1]

    newest = max(new_names, key=lambda n: after[n])
    return DOWNLOADS_DIR / newest


def open_in_browser(url: str, browser: str) -> None:
    if browser.lower() in ("default", ""):
        subprocess.run(["open", url], check=False)
    else:
        subprocess.run(["open", "-a", browser, url], check=False)


def run_ingest(pdf_path: Path, dry_run: bool = False) -> int:
    cmd = [sys.executable, str(INGEST_SCRIPT), "--pdf", str(pdf_path)]
    if dry_run:
        cmd.append("--dry-run")
    print(f"  → ingest: {pdf_path.name}")
    return subprocess.call(cmd)


def run_progress_counter() -> int:
    if not PROGRESS_SCRIPT.exists():
        return 0
    print("\nUpdating progress counter…")
    return subprocess.call([sys.executable, str(PROGRESS_SCRIPT)])


def wait_for_download(
    before: dict[str, float],
    glob_pattern: str,
    timeout: float,
    poll: float,
    session_start: float,
) -> Path | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        after = snapshot_pdfs(DOWNLOADS_DIR, glob_pattern, min_mtime=session_start - 5)
        found = find_new_pdf(before, after)
        if found and found.exists():
            # Brief settle — Safari may still be writing the file.
            time.sleep(0.8)
            if found.stat().st_size > 1024:
                return found
        time.sleep(poll)
    return None


def prompt_choice(message: str, choices: str = "Enter=next, s=skip, q=quit, r=retry") -> str:
    try:
        return input(f"  {message} [{choices}]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return "q"


def process_batch(args: argparse.Namespace) -> int:
    master_rows = load_csv(MASTER_PATH)
    plink_index = build_plink_index(master_rows)
    queue = load_queue(args.limit, args.start_rank)
    if not queue:
        print("No queue rows to process.")
        return 0

    if args.skip_ingested:
        queue = [
            row
            for row in queue
            if not master_has_pdf(master_rows, row.get("master_article_id", ""))
        ]
        if not queue:
            print("All rows in this batch already have PDFs in master.")
            return 0

    glob_pattern = "*.pdf" if args.any_pdf else "EBSCO-FullText*.pdf"
    session_start = time.time()
    known_pdfs = snapshot_pdfs(DOWNLOADS_DIR, glob_pattern)

    print(f"Batch: {len(queue)} articles (rank ≥ {args.start_rank})")
    print(f"Watching: {DOWNLOADS_DIR}/{glob_pattern}")
    print(f"Browser: {args.browser}")
    print()

    if args.open_all_tabs:
        for row in queue:
            url = article_url(row, plink_index)
            if url:
                open_in_browser(url, args.browser)
                time.sleep(args.tab_delay)
        print(f"Opened {len(queue)} tabs in {args.browser}. Download each PDF, then watch…\n")
        before = dict(known_pdfs)
        ingested = 0
        for _ in queue:
            pdf = wait_for_download(
                before, glob_pattern, args.wait, args.poll, session_start
            )
            if not pdf:
                choice = prompt_choice("No PDF detected — continue waiting?")
                if choice == "q":
                    break
                if choice == "r":
                    continue
                before = snapshot_pdfs(DOWNLOADS_DIR, glob_pattern)
                continue
            if not args.dry_run:
                run_ingest(pdf)
            before = snapshot_pdfs(DOWNLOADS_DIR, glob_pattern)
            known_pdfs.update(before)
            ingested += 1
            print(f"  ✓ ingested ({ingested}/{len(queue)})\n")
        if args.update_progress and ingested and not args.dry_run:
            run_progress_counter()
        return 0

    opened = 0
    ingested = 0
    skipped = 0

    for row in queue:
        rank = row.get("queue_rank", "?")
        mid = row.get("master_article_id", "")
        title = (row.get("title") or "")[:72]
        url = article_url(row, plink_index)

        if not url:
            print(f"[{rank}] SKIP {mid} — no ebsco_plink or DOI")
            skipped += 1
            continue

        print(f"[{rank}] {mid}: {title}")
        print(f"  {url}")

        if args.dry_run:
            continue

        before = snapshot_pdfs(DOWNLOADS_DIR, glob_pattern)
        open_in_browser(url, args.browser)
        opened += 1
        print(
            f"  Safari opened — download PDF "
            f"(EBSCO: Full Text → Download PDF). Waiting up to {int(args.wait)}s…"
        )

        pdf: Path | None = None
        while pdf is None:
            pdf = wait_for_download(
                before, glob_pattern, args.wait, args.poll, session_start
            )
            if pdf:
                break
            choice = prompt_choice(
                f"No new PDF in {int(args.wait)}s",
                "Enter=skip, r=retry wait, q=quit",
            )
            if choice == "q":
                print(f"\nStopped. opened={opened} ingested={ingested} skipped={skipped}")
                if args.update_progress and ingested:
                    run_progress_counter()
                return 0
            if choice == "r":
                before = snapshot_pdfs(DOWNLOADS_DIR, glob_pattern)
                pdf = wait_for_download(
                    before, glob_pattern, args.wait, args.poll, session_start
                )
                if pdf:
                    break
            skipped += 1
            pdf = None
            break

        if pdf is None:
            continue

        rc = run_ingest(pdf)
        if rc == 0:
            ingested += 1
            print(f"  ✓ done ({ingested} ingested this session)\n")
        else:
            print("  ! ingest returned non-zero — check output above\n")

        before = snapshot_pdfs(DOWNLOADS_DIR, glob_pattern)
        session_start = min(session_start, time.time() - 1)

    print(f"\nSession complete. opened={opened} ingested={ingested} skipped={skipped}")

    if args.update_progress and ingested and not args.dry_run:
        run_progress_counter()

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print batch URLs only")
    parser.add_argument("--limit", type=int, default=10, help="Articles per batch (default: 10)")
    parser.add_argument(
        "--start-rank",
        type=int,
        default=1,
        help="First queue_rank to process (default: 1)",
    )
    parser.add_argument(
        "--browser",
        default="Safari",
        help='macOS app to open URLs (default: Safari; use "default" for system browser)',
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=180.0,
        help="Seconds to wait for each PDF before prompting (default: 180)",
    )
    parser.add_argument(
        "--poll",
        type=float,
        default=1.5,
        help="Downloads folder poll interval in seconds (default: 1.5)",
    )
    parser.add_argument(
        "--any-pdf",
        action="store_true",
        help="Watch any new *.pdf in Downloads (not just EBSCO-FullText*.pdf)",
    )
    parser.add_argument(
        "--skip-ingested",
        action="store_true",
        default=True,
        help="Skip queue rows whose master row already has a PDF (default: on)",
    )
    parser.add_argument(
        "--no-skip-ingested",
        dest="skip_ingested",
        action="store_false",
        help="Process all queue rows even if master already has PDF",
    )
    parser.add_argument(
        "--open-all-tabs",
        action="store_true",
        help="Open entire batch in Safari tabs, then ingest as PDFs appear",
    )
    parser.add_argument(
        "--tab-delay",
        type=float,
        default=0.6,
        help="Delay between opening tabs when using --open-all-tabs (default: 0.6)",
    )
    parser.add_argument(
        "--update-progress",
        action="store_true",
        default=True,
        help="Run progress_counter.py after ingesting (default: on)",
    )
    parser.add_argument(
        "--no-update-progress",
        dest="update_progress",
        action="store_false",
        help="Do not refresh progress files after session",
    )
    args = parser.parse_args()
    return process_batch(args)


if __name__ == "__main__":
    raise SystemExit(main())
