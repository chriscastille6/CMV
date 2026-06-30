# EBSCO PDF Download Automation — Feasibility & Plan

**Date**: 2026-06-24  
**Status**: Semi-automated assistants available — not unattended bulk scraping.

---

## Direct answer

**SSO does not block you — but it blocks unattended automation.** Institutional login (OpenAthens, Shibboleth, campus SSO) is designed so sessions stay in *your* browser and cannot be copied to another engine. **The practical workaround is semi-automation: you stay logged in (Safari or a dedicated Chrome profile), scripts open the right URLs and ingest PDFs as they land.**

**Fully unattended download of ~485 remaining PDFs is not realistic or advisable** (MFA, captchas, publisher UI variance, library ToS).

---

## Recommended workflow for Safari users

**Best path if you already use Safari for EBSCO:** `watch_downloads_ingest.py`

This reuses your **existing Safari institutional session** — no Chrome profile, no Selenium, no cookie export.

### 5-minute setup

1. Confirm Safari is logged into EBSCO (open any `research.ebsco.com/plink/…` link — full text loads without re-login).
2. From the CMV repo root:

```bash
# Preview next batch
python3 review/EBSCO/watch_downloads_ingest.py --dry-run --limit 10

# Run a batch (opens one article at a time in Safari)
python3 review/EBSCO/watch_downloads_ingest.py --limit 10
```

3. For each article: in Safari, click **Download PDF** (or publisher equivalent). The script watches `~/Downloads` for `EBSCO-FullText*.pdf`, auto-ingests, and advances.
4. Progress files refresh automatically at end of batch (`progress_counter.py`).

### Keyboard / flow per article

| Step | You | Script |
|------|-----|--------|
| 1 | — | Opens `ebsco_plink` in Safari |
| 2 | Click Download PDF in Safari | Watches `~/Downloads` (up to 3 min) |
| 3 | — | Runs `ingest_uploaded_pdfs.py`, matches master ID |
| 4 | — | Opens next queue item |

If no PDF appears in time: press **r** to keep waiting, **Enter** to skip, **q** to quit.

### Variants

```bash
# Resume from queue rank 81
python3 review/EBSCO/watch_downloads_ingest.py --start-rank 81 --limit 10

# Publisher PDFs with non-EBSCO filenames (MDPI, Wiley, etc.)
python3 review/EBSCO/watch_downloads_ingest.py --limit 10 --any-pdf

# Power user: open 10 Safari tabs, download all, script ingests as files appear
python3 review/EBSCO/watch_downloads_ingest.py --limit 10 --open-all-tabs
```

### Expected time savings

| Mode | ~485 PDFs | Notes |
|------|-----------|-------|
| Fully manual (find link, download, run ingest, update progress) | ~8–12 h | Error-prone matching |
| **Safari watcher (batches of 10)** | **~4–6 h** | Correct URL every time; ingest automatic |
| SeleniumBase Chrome assistant | ~4–6 h | Same speed; requires one-time Chrome SSO login |

Savings come from **eliminating copy-paste of links and manual ingest runs**, not from removing the download click.

### Safari workflow limitations

- Still requires you at the keyboard for each PDF (or each tab batch).
- SSO session expires periodically — re-login in Safari when EBSCO asks.
- Some articles redirect to publishers; use `--any-pdf` if filenames are not `EBSCO-FullText-*.pdf`.
- 8 queue rows have no DOI/plink — handle separately after metadata import.

---

## Why Safari login does not transfer to automation

| Fact | Detail |
|------|--------|
| **Separate cookie jars** | Safari, Chrome, SeleniumBase, and Cursor's browser each store sessions independently. Cookies are not shared across apps. |
| **HttpOnly + Secure flags** | SSO cookies are often not readable/exportable by design. |
| **Device binding** | Some IdPs tie sessions to browser fingerprint or IP. |
| **Safari ITP** | Intelligent Tracking Prevention can shorten third-party cookie lifetime. |
| **Cookie export** | Manual export from Safari → import to Chrome **breaks often** and may violate policy. **Do not rely on it.** |

**What works instead:** run automation *inside* the browser where you're already authenticated — either Safari (`open -a Safari`) or Chrome with a **persistent `--user-data-dir` profile** after one manual login + MFA.

---

## SSO / auth — what works

| Approach | Verdict |
|----------|---------|
| **Safari + `watch_downloads_ingest.py`** | **Best for you** — uses active Safari session, zero extra login |
| One-time Chrome login + `--user-data-dir` profile | **Good** — session persists days–weeks; occasional re-MFA |
| `input("Press Enter after logging in…")` at script start | **Reliable** — used by `ebsco_download_assistant.py` |
| Zotero Connector in Safari/Chrome | **Good** — attaches PDF using live browser session + metadata |
| Unpaywall / DOI open-access fallback | **Partial** — ~20–40% hit rate for your pool; use when EBSCO has no PDF |
| Stored credentials / auto-login | **Do not do this** — security + MFA breakage |
| Cookie export from Safari | **Unreliable** — avoid |
| Fully unattended bulk scraping | **Not viable** — MFA, captchas, ToS |

**Cookie persistence (Chrome profile):** typically **days to a few weeks** depending on your institution's session timeout. Expect re-auth after laptop sleep, VPN change, or IdP policy. Safari institutional sessions behave similarly.

**OpenAthens / Shibboleth in automation:** scripts open the plink URL → browser hits IdP → **you complete login once** → subsequent plinks in the same browser reuse the session. The "pause-for-login" pattern at script start is the standard approach.

---

## Zotero alternative

If you prefer Zotero for metadata + PDF attachment:

1. Install **Zotero Connector** in Safari (you're already logged in).
2. Open queue URLs from `watch_downloads_ingest.py --dry-run` or export plinks from the CSV.
3. Click Connector → **Save to Zotero** (pulls PDF when available).
4. Export / link via existing `zotero_key` column in master.

**Pros:** excellent metadata, uses your live session. **Cons:** still one click per article; batch "Find Available PDF" hit rate varies for EBSCO-licensed content.

---

## Unpaywall / open-access fallback

For rows where EBSCO shows no full text, try open access before skipping:

```bash
# Manual: https://unpaywall.org/<DOI> or doi.org redirect
# ~413/421 queue rows have DOI — subset may have OA copies
```

This is a **fallback layer**, not a replacement for institutional EBSCO access. Ingest still works on any PDF you obtain.

---

## What does NOT work reliably

- Exporting Safari cookies and importing into Selenium/Chrome
- Running downloads while you sleep with no MFA/captcha handling
- Bulk scraping EBSCO at high rate (ToS / library AUP risk)
- One selector that clicks "Download PDF" across 400+ publisher sites (fragile; `ebsco_download_assistant.py --auto-click` is best-effort only)
- Transferring Cursor IDE browser session to Python automation

---

## Current CMV state

| Item | Value |
|------|------:|
| Screening pool | 570 |
| PDFs downloaded | 84 |
| Missing (master-linked) | 421 |
| **Remaining overall** | **485** (includes 64 pool-gap rows not yet in master) |
| Download queue rows | **421** (`review/EBSCO/download_queue_recent_first.csv`) |
| Queue with DOI | 413 |
| Queue without DOI | 8 |
| Master rows with `ebsco_plink` | 506 |

**Existing manual workflow (still works):**

1. Download from EBSCO → `~/Downloads/EBSCO-FullText-*.pdf`
2. `python3 review/EBSCO/ingest_uploaded_pdfs.py --scan-downloads`
3. `python3 review/master/progress_counter.py`

Ingest, matching (DOI → title+year), and progress tracking are solid. New scripts automate steps 1–3 in batches.

---

## EBSCO download flow

Articles resolve via **`ebsco_plink`** URLs in master, e.g. `https://research.ebsco.com/plink/<uuid>`.

After auth, flows vary:

- EBSCO HTML full text → **Download PDF** (`EBSCO-FullText-*.pdf`)
- Redirect to publisher (MDPI, Frontiers, Springer, Wiley, …)
- Open-access publisher → direct PDF
- No full text / embargo / database-only abstract

**Automation can open URLs and ingest PDFs; it cannot reliably click Download across 400+ publisher UIs.**

### Legal / ToS (brief)

- Library-licensed content; manual download for systematic review under institutional access is normal.
- Automated bulk retrieval may conflict with EBSCO/publisher/library acceptable-use policies.
- Treat scripts as **personal productivity assistants** (you at the keyboard), not unattended scrapers.

---

## SeleniumBase (Chrome alternative)

[SeleniumBase](https://github.com/seleniumbase/SeleniumBase) is a Python browser-automation framework. Relevant capabilities:

- `pip install seleniumbase` (+ Chrome)
- **`--user-data-dir=DIR`** — reuse a Chrome profile so institutional SSO persists across runs
- **`download_folder`** — direct download directory
- Does **not** solve MFA/captcha; user completes those in the browser

---

## Recommended approach (choose one)

| Priority | Tool | When to use |
|----------|------|-------------|
| **1** | `watch_downloads_ingest.py` | **Safari already logged in** (your case) |
| 2 | `ebsco_download_assistant.py` | Willing to log in once in dedicated Chrome profile |
| 3 | Manual + `ingest_uploaded_pdfs.py --scan-downloads` | Zero setup, slowest |

### Safari watcher — see top of this doc

### Chrome assistant setup

1. `pip install seleniumbase`; dedicated Chrome profile at `review/EBSCO/.browser_profile/`.
2. Script opens queue item → you download → press Enter to advance.
3. `--ingest-after-batch` runs ingest; progress counter refreshes.

---

## Usage

```bash
# Safari (recommended) — preview batch
python3 review/EBSCO/watch_downloads_ingest.py --dry-run --limit 10

# Safari — run batch
python3 review/EBSCO/watch_downloads_ingest.py --limit 10

# Chrome / SeleniumBase — one-time: pip install seleniumbase
python3 review/EBSCO/ebsco_download_assistant.py --limit 10 --ingest-after-batch
python3 review/EBSCO/ebsco_download_assistant.py --start-rank 50
```

**Chrome profile** defaults to `review/EBSCO/.browser_profile/` (gitignored).

---

## Out of scope for v0

- Unattended login or credential storage
- Publisher-specific selector library
- Parallel browsers / multi-worker downloads
- Pool-gap rows without `ebsco_plink` (import metadata batch 251–300 first)

---

## Pilot checklist (10 articles)

- [ ] Safari opens plinks without re-login
- [ ] ≥7/10 PDFs land in Downloads with recognizable names
- [ ] Ingest matches master IDs without `--force-master-id`
- [ ] Progress counter shows updated download counts

If publisher redirects dominate, use `--any-pdf` or Zotero Connector for those rows.
