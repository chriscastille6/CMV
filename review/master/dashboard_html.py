"""HTML template generation for PROGRESS_DASHBOARD.html."""

from __future__ import annotations

import json


def format_dashboard_html(
    payload: dict,
    results_payload: dict,
    prisma_payload: dict,
    on_hand_payload: dict,
    worklist_payload: dict,
    ebsco_150_summary_payload: dict,
) -> str:
    embedded = json.dumps(payload, indent=2)
    results_embedded = json.dumps(results_payload, indent=2)
    prisma_embedded = json.dumps(prisma_payload, indent=2)
    on_hand_embedded = json.dumps(on_hand_payload, indent=2)
    worklist_embedded = json.dumps(worklist_payload, indent=2)
    ebsco_150_embedded = json.dumps(ebsco_150_summary_payload, indent=2)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>EBSCO 1–150 Screening Progress</title>
  <style>
    :root {{
      --bg: #f6f7f9;
      --card: #ffffff;
      --text: #1a1d21;
      --muted: #5c6570;
      --accent: #2563eb;
      --accent-soft: #dbeafe;
      --bar-bg: #e5e7eb;
      --border: #e2e8f0;
      --success: #059669;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}
    .wrap {{ max-width: 960px; margin: 0 auto; padding: 2rem 1.25rem 3rem; }}
    h1 {{ margin: 0 0 0.25rem; font-size: 1.75rem; font-weight: 700; }}
    .subtitle {{ color: var(--muted); margin: 0 0 1.75rem; font-size: 0.95rem; }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin-bottom: 1.75rem;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.25rem 1.35rem;
      box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }}
    .card-label {{ font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); margin-bottom: 0.35rem; }}
    .card-value {{ font-size: 2rem; font-weight: 700; line-height: 1.1; }}
    .card-value small {{ font-size: 1.1rem; font-weight: 500; color: var(--muted); }}
    .progress-block {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem 1.35rem; margin-bottom: 1rem; }}
    .progress-header {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.5rem; }}
    .progress-header h2 {{ margin: 0; font-size: 1rem; font-weight: 600; }}
    .progress-header span {{ color: var(--muted); font-size: 0.9rem; }}
    .bar {{ height: 12px; background: var(--bar-bg); border-radius: 999px; overflow: hidden; }}
    .bar-fill {{ height: 100%; background: linear-gradient(90deg, var(--accent), #3b82f6); border-radius: 999px; transition: width 0.4s ease; }}
    .bar-fill.exam {{ background: linear-gradient(90deg, var(--success), #34d399); }}
    .tables {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; margin: 1.75rem 0; }}
    table {{ width: 100%; border-collapse: collapse; background: var(--card); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }}
    th, td {{ padding: 0.65rem 1rem; text-align: left; border-bottom: 1px solid var(--border); }}
    th {{ background: #f8fafc; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); }}
    tr:last-child td {{ border-bottom: none; }}
    td.count {{ text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; }}
    .meta {{ background: var(--accent-soft); border-radius: 10px; padding: 1rem 1.15rem; font-size: 0.9rem; color: #1e3a5f; margin-bottom: 1rem; }}
    .instructions {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.15rem 1.35rem; font-size: 0.9rem; color: var(--muted); }}
    .instructions code {{ background: #f1f5f9; padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.85rem; }}
    .fetch-mode {{ font-size: 0.8rem; color: var(--muted); margin-top: 0.75rem; }}
    #fetch-status {{ font-weight: 600; }}
    .tabs {{
      display: flex;
      gap: 0.5rem;
      margin-bottom: 1.25rem;
      border-bottom: 1px solid var(--border);
      padding-bottom: 0;
    }}
    .tab {{
      background: none;
      border: none;
      border-bottom: 2px solid transparent;
      padding: 0.65rem 1rem;
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--muted);
      cursor: pointer;
      margin-bottom: -1px;
    }}
    .tab.active {{
      color: var(--accent);
      border-bottom-color: var(--accent);
    }}
    .tab-panel {{ display: none; }}
    .tab-panel.active {{ display: block; }}
    .results-header {{
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      justify-content: space-between;
      gap: 0.75rem;
      margin-bottom: 1rem;
    }}
    .results-header h2 {{ margin: 0; font-size: 1.1rem; }}
    .results-count {{ color: var(--muted); font-size: 0.9rem; }}
    .filter-input {{
      width: 100%;
      max-width: 320px;
      padding: 0.5rem 0.75rem;
      border: 1px solid var(--border);
      border-radius: 8px;
      font-size: 0.9rem;
      margin-bottom: 1rem;
    }}
    .results-section {{ margin-bottom: 2rem; }}
    .results-section h3 {{
      margin: 0 0 0.75rem;
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--text);
    }}
    .table-scroll {{ overflow-x: auto; border-radius: 12px; border: 1px solid var(--border); }}
    .results-table {{ border: none; border-radius: 0; min-width: 1200px; }}
    .results-table th {{
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
    }}
    .results-table th:hover {{ background: #eef2f7; }}
    .results-table th.sorted-asc::after {{ content: " ▲"; font-size: 0.65rem; }}
    .results-table th.sorted-desc::after {{ content: " ▼"; font-size: 0.65rem; }}
    .results-table td {{
      font-size: 0.85rem;
      max-width: 220px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .results-table td.title-cell {{ max-width: 280px; }}
    .summary-section {{ margin-bottom: 1.75rem; }}
    .summary-section h3 {{
      margin: 0 0 0.5rem;
      font-size: 0.95rem;
      font-weight: 600;
    }}
    .summary-note {{
      margin: 0 0 0.65rem;
      font-size: 0.85rem;
      color: var(--muted);
    }}
    .summary-table {{ margin-bottom: 0; }}
    .summary-table td.count, .summary-table td.pct {{ text-align: right; font-variant-numeric: tabular-nums; }}
    .evidence-cell {{ max-width: 360px; white-space: normal; font-size: 0.82rem; color: var(--muted); }}
    details.worklist-evidence {{ margin: 1rem 0 1.5rem; }}
    details.worklist-evidence summary {{ cursor: pointer; font-weight: 600; margin-bottom: 0.5rem; }}
    .prevalence-block {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem 1.35rem; margin-bottom: 1rem; }}
    .prevalence-block h3 {{ margin: 0 0 0.75rem; font-size: 0.95rem; font-weight: 600; }}
    .prevalence-row {{ display: grid; grid-template-columns: minmax(140px, 1fr) 1fr 3.5rem; gap: 0.65rem; align-items: center; margin-bottom: 0.45rem; font-size: 0.85rem; }}
    .prevalence-label {{ color: var(--text); }}
    .prevalence-bar {{ height: 10px; background: var(--bar-bg); border-radius: 999px; overflow: hidden; }}
    .prevalence-bar-fill {{ height: 100%; background: linear-gradient(90deg, var(--success), #34d399); border-radius: 999px; min-width: 2px; }}
    .prevalence-pct {{ text-align: right; font-variant-numeric: tabular-nums; color: var(--muted); font-size: 0.82rem; }}
    .funnel-row {{ display: grid; grid-template-columns: minmax(120px, 1fr) 1fr 3.5rem; gap: 0.65rem; align-items: center; margin-bottom: 0.45rem; font-size: 0.85rem; }}
    .funnel-bar-fill {{ height: 100%; background: linear-gradient(90deg, var(--accent), #3b82f6); border-radius: 999px; min-width: 2px; }}
    .extraction-summary-scope {{ margin-bottom: 2rem; }}
    .extraction-summary-scope > h3 {{ margin: 0 0 0.35rem; font-size: 1rem; font-weight: 600; }}
    .scope-meta {{ color: var(--muted); font-size: 0.85rem; margin: 0 0 1rem; }}
    .rq-group {{ margin: 1.25rem 0 1.5rem; }}
    .rq-group > h4 {{ margin: 0 0 0.75rem; font-size: 0.92rem; font-weight: 600; color: var(--accent); }}
    .histogram-row {{ display: grid; grid-template-columns: 4.5rem 1fr 2.5rem; gap: 0.5rem; align-items: end; margin-bottom: 0.35rem; font-size: 0.82rem; }}
    .histogram-bar-wrap {{ height: 72px; display: flex; align-items: flex-end; background: var(--bar-bg); border-radius: 6px 6px 0 0; overflow: hidden; }}
    .histogram-bar {{ width: 100%; background: linear-gradient(180deg, #60a5fa, var(--accent)); border-radius: 4px 4px 0 0; min-height: 2px; }}
    .histogram-count {{ text-align: right; font-variant-numeric: tabular-nums; color: var(--muted); }}
    .visual-note {{ color: var(--muted); font-size: 0.82rem; margin: 0 0 0.65rem; }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg: #0f1419;
        --card: #1a2332;
        --text: #e8eaed;
        --muted: #9aa0a6;
        --accent: #60a5fa;
        --accent-soft: #1e3a5f;
        --bar-bg: #2d3748;
        --border: #2d3748;
        --success: #34d399;
      }}
      th {{ background: #1e293b; }}
      .results-table th:hover {{ background: #334155; }}
      .instructions code {{ background: #1e293b; }}
      .meta {{ color: #bfdbfe; }}
      .prisma-box {{ background: var(--card); }}
      .prisma-side-box {{ background: #1e293b; }}
    }}
    .prisma-header {{
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      justify-content: space-between;
      gap: 0.75rem;
      margin-bottom: 1rem;
    }}
    .prisma-header h2 {{ margin: 0; font-size: 1.1rem; }}
    .prisma-strand {{ color: var(--muted); font-size: 0.85rem; }}
    .prisma-flow {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0;
      margin: 1.5rem 0 2rem;
    }}
    .prisma-stage {{
      width: 100%;
      max-width: 520px;
      position: relative;
    }}
    .prisma-stage-row {{
      display: flex;
      align-items: stretch;
      gap: 1rem;
      width: 100%;
    }}
    .prisma-box {{
      flex: 1;
      background: var(--card);
      border: 2px solid var(--border);
      border-radius: 10px;
      padding: 1rem 1.15rem;
      text-align: center;
    }}
    .prisma-box-label {{
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      color: var(--muted);
      margin-bottom: 0.35rem;
    }}
    .prisma-box-title {{
      font-size: 0.95rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
      line-height: 1.35;
    }}
    .prisma-count {{
      font-size: 1.75rem;
      font-weight: 700;
      font-variant-numeric: tabular-nums;
      color: var(--accent);
    }}
    .prisma-count small {{
      font-size: 0.95rem;
      font-weight: 500;
      color: var(--muted);
    }}
    .prisma-sub {{
      margin-top: 0.45rem;
      font-size: 0.8rem;
      color: var(--muted);
    }}
    .prisma-side-box {{
      flex: 0 0 200px;
      background: #f8fafc;
      border: 2px dashed var(--border);
      border-radius: 10px;
      padding: 0.85rem 1rem;
      text-align: center;
      align-self: center;
    }}
    .prisma-side-box .prisma-count {{
      font-size: 1.35rem;
      color: var(--muted);
    }}
    .prisma-arrow {{
      text-align: center;
      color: var(--muted);
      font-size: 1.25rem;
      line-height: 1;
      padding: 0.35rem 0;
    }}
    .prisma-note {{
      background: var(--accent-soft);
      border-radius: 10px;
      padding: 1rem 1.15rem;
      font-size: 0.9rem;
      margin-top: 1rem;
      line-height: 1.5;
    }}
    .prisma-legend {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 0.75rem;
      margin-top: 1.25rem;
    }}
    .prisma-legend-item {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.65rem 0.85rem;
      font-size: 0.85rem;
    }}
    .prisma-legend-item strong {{
      display: block;
      font-variant-numeric: tabular-nums;
      font-size: 1.1rem;
      margin-bottom: 0.15rem;
    }}
    .tabs-scroll {{
      overflow-x: auto;
      flex-wrap: nowrap;
      -webkit-overflow-scrolling: touch;
      scrollbar-width: thin;
    }}
    .tabs-scroll .tab {{
      flex-shrink: 0;
      white-space: nowrap;
      font-size: 0.88rem;
      padding: 0.6rem 0.85rem;
    }}
    .overview-strand {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.15rem 1.25rem;
      margin-bottom: 1rem;
    }}
    .overview-strand h3 {{
      margin: 0 0 0.75rem;
      font-size: 0.95rem;
      font-weight: 600;
    }}
    .overview-strand .cards {{ margin-bottom: 0.75rem; }}
    .overview-link {{
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--accent);
      text-decoration: none;
    }}
    .overview-link:hover {{ text-decoration: underline; }}
    .quick-links {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem 1rem;
      margin: 1rem 0 1.5rem;
      font-size: 0.85rem;
    }}
    .quick-links a {{
      color: var(--accent);
      text-decoration: none;
      font-weight: 600;
    }}
    .quick-links a:hover {{ text-decoration: underline; }}
    .sticky-toc {{
      position: sticky;
      top: 0;
      z-index: 20;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 0.65rem 1rem;
      margin-bottom: 1.25rem;
      font-size: 0.82rem;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.35rem 0.65rem;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    .sticky-toc strong {{
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--muted);
      margin-right: 0.25rem;
    }}
    .sticky-toc a {{
      color: var(--accent);
      text-decoration: none;
      white-space: nowrap;
    }}
    .sticky-toc a:hover {{ text-decoration: underline; }}
    .section-anchor {{ scroll-margin-top: 5rem; }}
    details.collapsible-rq {{
      margin: 1rem 0 1.25rem;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 0.5rem 0.85rem 0.85rem;
      background: var(--card);
    }}
    details.collapsible-rq > summary {{
      cursor: pointer;
      font-weight: 600;
      font-size: 0.92rem;
      color: var(--accent);
      padding: 0.35rem 0;
      list-style-position: outside;
    }}
    details.collapsible-table {{
      margin-bottom: 0.85rem;
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
    }}
    details.collapsible-table > summary {{
      cursor: pointer;
      font-weight: 600;
      font-size: 0.88rem;
      padding: 0.55rem 0.85rem;
      background: #f8fafc;
    }}
    @media (prefers-color-scheme: dark) {{
      details.collapsible-table > summary {{ background: #1e293b; }}
    }}
    details.collapsible-table[open] > summary {{
      border-bottom: 1px solid var(--border);
    }}
    details.collapsible-table .summary-table {{
      border: none;
      border-radius: 0;
    }}
    @media (max-width: 640px) {{
      .wrap {{ padding: 1.25rem 0.85rem 2rem; }}
      .sticky-toc {{ font-size: 0.78rem; padding: 0.55rem 0.75rem; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>ULMC Review Progress</h1>
    <p class="subtitle">EBSCO 1–150 screening · extraction descriptives · 570-pool download/examination</p>

    <div class="meta">
      Last updated: <strong id="last-updated">—</strong>
      <span class="fetch-mode"> · <span id="fetch-status">loading…</span></span>
    </div>

    <div class="tabs tabs-scroll">
      <button type="button" class="tab active" data-tab="overview">Overview</button>
      <button type="button" class="tab" data-tab="screening-1150">EBSCO 1–150 Screening</button>
      <button type="button" class="tab" data-tab="results-1150">EBSCO 1–150 Results</button>
      <button type="button" class="tab" data-tab="progress">Full 570 Pool</button>
      <button type="button" class="tab" data-tab="prisma">PRISMA Flow</button>
      <button type="button" class="tab" data-tab="datasets">Datasets</button>
    </div>

    <div id="tab-overview" class="tab-panel active">
      <div class="results-header">
        <h2>Progress overview</h2>
        <span class="results-count">Cross-strand snapshot</span>
      </div>
      <div class="quick-links" id="overview-quick-links">
        <strong>Jump to:</strong>
        <a href="#tab-screening-1150" data-goto-tab="screening-1150">Screening</a>
        <a href="#tab-results-1150" data-goto-tab="results-1150">RQ results (n=77)</a>
        <a href="#tab-progress" data-goto-tab="progress">570 pool</a>
        <a href="#tab-prisma" data-goto-tab="prisma">PRISMA</a>
        <a href="#tab-datasets" data-goto-tab="datasets">Datasets</a>
      </div>
      <div id="overview-strands"></div>
      <div style="margin-top: 1.5rem; border-top: 1px solid var(--border); padding-top: 1.5rem;">
        <div class="results-header">
          <h2>On-hand examination cohort</h2>
          <span class="results-count" id="on-hand-updated">—</span>
        </div>
        <div class="meta" id="on-hand-holdout-note"></div>
        <div class="cards" id="on-hand-cards"></div>
        <div class="tables">
          <div>
            <table>
              <thead><tr><th colspan="2">Level 1 screening (cohort)</th></tr></thead>
              <tbody id="on-hand-l1-table"></tbody>
            </table>
          </div>
          <div>
            <table>
              <thead><tr><th colspan="2">examination_status (cohort)</th></tr></thead>
              <tbody id="on-hand-exam-table"></tbody>
            </table>
          </div>
        </div>
        <div class="instructions" style="margin-top:1rem">
          <strong>On-hand cohort docs</strong><br>
          Definition: <a href="EBSCO/EXAMINATION_COHORT_ON_HAND.md" id="on-hand-doc-link">EXAMINATION_COHORT_ON_HAND.md</a> ·
          Extraction: <a href="EBSCO/systematic_extraction_ebsco_on_hand.csv" id="on-hand-extraction-link">systematic_extraction_ebsco_on_hand.csv</a> ·
          Source: <code id="on-hand-cohort-source">—</code>
        </div>
      </div>
    </div>

    <div id="tab-screening-1150" class="tab-panel">
      <div class="results-header">
        <h2>EBSCO 1–150 screening</h2>
        <span class="results-count" id="worklist-updated">—</span>
      </div>
      <div class="meta" id="worklist-definition"></div>
      <div class="cards" id="worklist-cards"></div>
      <div class="progress-block">
        <div class="progress-header">
          <h2>L1 scanned (decision + evidence)</h2>
          <span id="worklist-scanned-pct-label">—</span>
        </div>
        <div class="bar"><div class="bar-fill" id="worklist-scanned-bar" style="width:0%"></div></div>
      </div>
      <div class="prevalence-block" id="ebsco-150-l1-funnel"></div>
      <div id="worklist-summary-sections"></div>
      <details class="worklist-evidence" open>
        <summary>Verification sample (3 papers)</summary>
        <div id="worklist-verification"></div>
      </details>
      <details class="worklist-evidence">
        <summary>Screening evidence table (first 50 rows)</summary>
        <p class="summary-note" id="worklist-evidence-note"></p>
        <div id="worklist-evidence-table"></div>
      </details>
      <div class="instructions">
        <strong>Classification review</strong><br>
        Verification: <a href="EBSCO/VERIFICATION_SAMPLE.md" id="worklist-verification-link">VERIFICATION_SAMPLE.md</a><br>
        Full evidence: <code id="worklist-evidence-path">review/EBSCO/ebsco_150_screening_evidence.csv</code><br>
        Queue: <a href="EBSCO/CLASSIFICATION_REVIEW.md" id="worklist-review-link">CLASSIFICATION_REVIEW.md</a><br>
        Feedback CSV: <code>review/EBSCO/classification_feedback.csv</code> ·
        Apply: <code>python3 review/EBSCO/apply_classification_feedback.py</code><br><br>
        <a href="#tab-results-1150" class="overview-link" data-goto-tab="results-1150">→ Extraction descriptives &amp; RQ tables</a>
      </div>
    </div>

    <div id="tab-results-1150" class="tab-panel">
      <div class="results-header">
        <h2>EBSCO 1–150 extraction results</h2>
        <span class="results-count" id="ebsco-150-summary-updated">—</span>
      </div>
      <nav class="sticky-toc" id="results-toc" aria-label="Results table of contents"></nav>
      <div class="cards" id="ebsco-150-coding-cards"></div>
      <div id="ebsco-150-extraction-summary"></div>
      <div class="instructions" style="margin-top:1.25rem">
        <strong>Refresh</strong>: re-run extraction, then <code>python3 review/master/progress_counter.py</code><br>
        <a href="#tab-screening-1150" class="overview-link" data-goto-tab="screening-1150">← Back to screening funnel &amp; evidence</a>
      </div>
    </div>

    <div id="tab-progress" class="tab-panel">
    <div class="cards">
      <div class="card">
        <div class="card-label">Downloaded</div>
        <div class="card-value"><span id="downloaded">—</span> <small>/ <span id="pool-size">570</span></small></div>
      </div>
      <div class="card">
        <div class="card-label">Remaining download</div>
        <div class="card-value" id="remaining-download">—</div>
      </div>
      <div class="card">
        <div class="card-label">Fully coded</div>
        <div class="card-value" id="fully-coded">—</div>
      </div>
      <div class="card">
        <div class="card-label">Remaining examine</div>
        <div class="card-value" id="remaining-examine">—</div>
      </div>
    </div>

    <div class="progress-block">
      <div class="progress-header">
        <h2>PDF download progress</h2>
        <span id="download-pct-label">—</span>
      </div>
      <div class="bar"><div class="bar-fill" id="download-bar" style="width:0%"></div></div>
    </div>

    <div class="progress-block">
      <div class="progress-header">
        <h2>Examination progress (fully coded)</h2>
        <span id="exam-pct-label">—</span>
      </div>
      <div class="bar"><div class="bar-fill exam" id="exam-bar" style="width:0%"></div></div>
    </div>

    <div class="tables">
      <div>
        <table>
          <thead><tr><th colspan="2">examination_status</th></tr></thead>
          <tbody id="exam-table"></tbody>
        </table>
      </div>
      <div>
        <table>
          <thead><tr><th colspan="2">pdf_status (in master)</th></tr></thead>
          <tbody id="pdf-table"></tbody>
        </table>
      </div>
    </div>

    <div class="instructions">
      <strong>Refresh data</strong><br>
      Re-run <code>python3 review/master/progress_counter.py</code>, then refresh this page.<br><br>
      <strong>Auto-refresh (optional)</strong><br>
      Browsers block <code>file://</code> JSON fetch — this page uses embedded data from the last counter run.
      For live 30s polling, serve the <code>review/</code> folder:<br>
      <code>cd review &amp;&amp; python3 -m http.server 8765</code> → open
      <code>http://localhost:8765/PROGRESS_DASHBOARD.html</code>
    </div>
    </div>

    <div id="tab-prisma" class="tab-panel">
      <div class="prisma-header">
        <h2>PRISMA 2020 flow — EBSCO 1–150 (to date)</h2>
        <span class="prisma-strand" id="prisma-updated">—</span>
      </div>
      <div class="prisma-flow" id="prisma-flow"></div>
      <div class="prisma-note" id="prisma-included-note"></div>
      <div class="prisma-legend" id="prisma-legend"></div>
      <div class="instructions" style="margin-top:1.25rem">
        <strong>Source</strong>: <code id="prisma-source-doc">—</code> ·
        Static diagram: <code>review/EBSCO/PRISMA2020_final.svg</code><br>
        Live counts refresh with <code>python3 review/master/progress_counter.py</code>.
      </div>
    </div>

    <div id="tab-datasets" class="tab-panel">
      <div class="results-header">
        <h2>Fully coded articles</h2>
        <span class="results-count" id="results-count-label">—</span>
      </div>
      <input type="search" class="filter-input" id="results-filter" placeholder="Filter by title, author, journal, DOI…" autocomplete="off">
      <div id="results-sections"></div>
      <div class="empty-state" id="results-empty" style="display:none">No fully coded articles yet. Re-run the counter after extraction updates.</div>
    </div>
  </div>

  <script type="application/json" id="dashboard-data">{embedded}</script>
  <script type="application/json" id="results-data">{results_embedded}</script>
  <script type="application/json" id="prisma-data">{prisma_embedded}</script>
  <script type="application/json" id="on-hand-data">{on_hand_embedded}</script>
  <script type="application/json" id="worklist-data">{worklist_embedded}</script>
  <script type="application/json" id="ebsco-150-summary-data">{ebsco_150_embedded}</script>
  <script>
    const EMBEDDED = JSON.parse(document.getElementById("dashboard-data").textContent);
    const RESULTS_EMBEDDED = JSON.parse(document.getElementById("results-data").textContent);
    const PRISMA_EMBEDDED = JSON.parse(document.getElementById("prisma-data").textContent);
    const ON_HAND_EMBEDDED = JSON.parse(document.getElementById("on-hand-data").textContent);
    const WORKLIST_EMBEDDED = JSON.parse(document.getElementById("worklist-data").textContent);
    const EBSCO_150_SUMMARY_EMBEDDED = JSON.parse(document.getElementById("ebsco-150-summary-data").textContent);
    const JSON_URL = "progress_dashboard_data.json";
    const PRISMA_URL = "prisma_flow_data.json";
    const RESULTS_URL = "progress_results_data.json";
    const ON_HAND_URL = "ebsco_on_hand_cohort_data.json";
    const WORKLIST_URL = "ebsco_worklist_1_150_data.json";
    const EBSCO_150_SUMMARY_URL = "progress_ebsco_150_summary_data.json";
    const REFRESH_MS = 30000;
    let resultsData = RESULTS_EMBEDDED;
    let prismaData = PRISMA_EMBEDDED;
    let onHandData = ON_HAND_EMBEDDED;
    let worklistData = WORKLIST_EMBEDDED;
    let ebsco150SummaryData = EBSCO_150_SUMMARY_EMBEDDED;
    let progressData = EMBEDDED;
    let resultsFilter = "";
    const sortState = {{}};

    function fmtTime(iso) {{
      if (!iso) return "—";
      try {{
        return new Date(iso).toLocaleString();
      }} catch (_) {{
        return iso;
      }}
    }}

    function renderTable(tbodyId, counts) {{
      const tbody = document.getElementById(tbodyId);
      tbody.innerHTML = "";
      const entries = Object.entries(counts || {{}}).sort((a, b) => b[1] - a[1]);
      for (const [status, count] of entries) {{
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${{status || "(empty)"}}</td><td class="count">${{count}}</td>`;
        tbody.appendChild(tr);
      }}
      if (!entries.length) {{
        tbody.innerHTML = '<tr><td colspan="2">No data</td></tr>';
      }}
    }}

    function render(data, source) {{
      progressData = data;
      document.getElementById("last-updated").textContent = fmtTime(data.last_updated);
      document.getElementById("pool-size").textContent = data.pool_size;
      document.getElementById("downloaded").textContent = data.pdf_downloaded;
      document.getElementById("remaining-download").textContent = data.remaining_to_download;
      document.getElementById("fully-coded").textContent = data.exam_fully_coded;
      document.getElementById("remaining-examine").textContent = data.remaining_to_examine;
      document.getElementById("download-pct-label").textContent = data.download_pct + "%";
      document.getElementById("exam-pct-label").textContent = data.examination_pct + "%";
      document.getElementById("download-bar").style.width = data.download_pct + "%";
      document.getElementById("exam-bar").style.width = data.examination_pct + "%";
      renderTable("exam-table", data.examination_status_counts);
      renderTable("pdf-table", data.pdf_status_counts);
      document.getElementById("fetch-status").textContent = source;
      renderOverview();
    }}

    function escHtml(value) {{
      return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }}

    function studyMatchesFilter(study, query) {{
      if (!query) return true;
      const hay = [
        study.title, study.authors, study.journal, study.doi,
        study.study_order, study.legacy_refid, study.statistical_methods_mv,
        study.author_conclusion_mv, study.estimator, study.pls_cbsem_category,
        study.notes,
      ].join(" ").toLowerCase();
      return hay.includes(query);
    }}

    function compareValues(a, b, col) {{
      const av = (a[col] ?? "").toString().toLowerCase();
      const bv = (b[col] ?? "").toString().toLowerCase();
      if (col === "year") {{
        const an = parseInt(av, 10) || 0;
        const bn = parseInt(bv, 10) || 0;
        return an - bn;
      }}
      if (av < bv) return -1;
      if (av > bv) return 1;
      return 0;
    }}

    function sortStudies(studies, tableId) {{
      const state = sortState[tableId];
      if (!state) return studies;
      const sorted = [...studies];
      sorted.sort((a, b) => {{
        const cmp = compareValues(a, b, state.col);
        return state.dir === "asc" ? cmp : -cmp;
      }});
      return sorted;
    }}

    function renderResultsTable(tableId, studies, columns, labels) {{
      const sorted = sortStudies(studies, tableId);
      const rows = sorted.map((study) => {{
        const cells = columns.map((col) => {{
          const raw = study[col] ?? "";
          const cls = col === "title" ? "title-cell" : "";
          return `<td class="${{cls}}" title="${{escHtml(raw)}}">${{escHtml(raw) || "—"}}</td>`;
        }}).join("");
        return `<tr>${{cells}}</tr>`;
      }}).join("");
      const headers = columns.map((col) => {{
        const state = sortState[tableId];
        let cls = "";
        if (state && state.col === col) {{
          cls = state.dir === "asc" ? "sorted-asc" : "sorted-desc";
        }}
        const label = labels[col] || col;
        return `<th data-col="${{col}}" class="${{cls}}">${{escHtml(label)}}</th>`;
      }}).join("");
      return `
        <div class="table-scroll">
          <table class="results-table" id="${{tableId}}">
            <thead><tr>${{headers}}</tr></thead>
            <tbody>${{rows || '<tr><td colspan="' + columns.length + '">No matching rows</td></tr>'}}</tbody>
          </table>
        </div>`;
    }}

    function attachSortHandlers(tableId) {{
      const table = document.getElementById(tableId);
      if (!table) return;
      table.querySelectorAll("th[data-col]").forEach((th) => {{
        th.addEventListener("click", () => {{
          const col = th.dataset.col;
          const prev = sortState[tableId];
          if (prev && prev.col === col) {{
            sortState[tableId] = {{ col, dir: prev.dir === "asc" ? "desc" : "asc" }};
          }} else {{
            sortState[tableId] = {{ col, dir: "asc" }};
          }}
          renderResults(resultsData);
        }});
      }});
    }}

    function summaryRowCells(row, cols) {{
      if (Array.isArray(row)) return row;
      if (row.cells) return row.cells;
      if (cols && cols.length) return cols.map((c) => row[c] ?? "");
      return [];
    }}

    function renderSummaryTable(table, opts) {{
      const collapsible = opts && opts.collapsible;
      const cols = table.columns || [];
      const headers = cols.map((c) => `<th>${{escHtml(c)}}</th>`).join("");
      const rows = (table.rows || []).map((row) => {{
        const cells = summaryRowCells(row, cols).map((cell, i) => {{
          const cls = i === 1 ? "count" : (i === 2 ? "pct" : "");
          return `<td class="${{cls}}">${{escHtml(cell) || "—"}}</td>`;
        }}).join("");
        return `<tr>${{cells}}</tr>`;
      }}).join("");
      const note = table.note
        ? `<p class="summary-note">${{escHtml(table.note)}}</p>`
        : "";
      const tableHtml = `
          <table class="summary-table">
            <thead><tr>${{headers}}</tr></thead>
            <tbody>${{rows || '<tr><td colspan="' + cols.length + '">No data</td></tr>'}}</tbody>
          </table>`;
      if (collapsible) {{
        return `
        <details class="collapsible-table">
          <summary>${{escHtml(table.title)}}</summary>
          ${{note}}
          ${{tableHtml}}
        </details>`;
      }}
      return `
        <div class="summary-section">
          <h3>${{escHtml(table.title)}}</h3>
          ${{note}}
          ${{tableHtml}}
        </div>`;
    }}

    function renderResults(data) {{
      resultsData = data;
      const query = resultsFilter.trim().toLowerCase();
      const columns = data.columns || [];
      const labels = data.column_labels || {{}};
      const total = data.total_count || 0;
      document.getElementById("results-count-label").textContent =
        `${{total}} fully coded article${{total === 1 ? "" : "s"}}`;

      const sections = [];
      const legacy = (data.legacy_studies || []).filter((s) => studyMatchesFilter(s, query));
      const pool = (data.ebsco_pool_studies || []).filter((s) => studyMatchesFilter(s, query));
      const other = (data.other_studies || []).filter((s) => studyMatchesFilter(s, query));

      if (legacy.length) {{
        sections.push(`
          <div class="results-section">
            <h3>Legacy 182 fully coded (${{legacy.length}})</h3>
            ${{renderResultsTable("results-legacy", legacy, columns, labels)}}
          </div>`);
      }}
      if (pool.length) {{
        sections.push(`
          <div class="results-section">
            <h3>EBSCO 570-pool fully coded (${{pool.length}})</h3>
            ${{renderResultsTable("results-pool", pool, columns, labels)}}
          </div>`);
      }} else if (total > 0 && legacy.length) {{
        sections.push(`
          <div class="results-section">
            <p class="results-count">No fully coded articles in the EBSCO pool yet. Showing legacy extraction data below.</p>
          </div>`);
      }}
      if (other.length) {{
        sections.push(`
          <div class="results-section">
            <h3>Other fully coded (${{other.length}})</h3>
            ${{renderResultsTable("results-other", other, columns, labels)}}
          </div>`);
      }}

      const container = document.getElementById("results-sections");
      const empty = document.getElementById("results-empty");
      if (!total) {{
        container.innerHTML = "";
        empty.style.display = "block";
        return;
      }}
      empty.style.display = "none";
      container.innerHTML = sections.join("");
      ["results-legacy", "results-pool", "results-other"].forEach(attachSortHandlers);
    }}

    function renderPrisma(data) {{
      prismaData = data;
      document.getElementById("prisma-updated").textContent =
        "Updated " + fmtTime(data.last_updated);
      document.getElementById("prisma-source-doc").textContent = data.source_doc || "—";
      const note = [data.included_note, data.legacy_strand_note].filter(Boolean).join(" ");
      document.getElementById("prisma-included-note").textContent = note;

      const fmt = (n) => (n ?? 0).toLocaleString();
      const is1150 = data.strand === "ebsco_worklist_positions_1_150";

      const stages = is1150 ? [
        {{
          type: "branch",
          main: {{
            label: "Identification",
            title: "Records identified (EBSCO export 1–150)",
            count: fmt(data.identified),
          }},
          side: {{
            label: "Removed",
            title: "Off-pool (not in 570 registry)",
            count: fmt(data.off_pool_removed),
          }},
        }},
        {{
          label: "Retrieval",
          title: "Reports sought / PDFs retrieved (in-pool)",
          count: fmt(data.pdfs_retrieved),
          sub: `${{fmt(data.in_pool)}} in-pool at positions 1–150`,
        }},
        {{
          label: "Eligibility",
          title: "Reports assessed for eligibility (Level 1)",
          count: fmt(data.full_text_assessed),
          sub: `${{fmt(data.l1_excluded_total)}} excluded (${{fmt(data.l1_excluded)}} eligibility + ${{fmt(data.l1_excluded_pls)}} PLS) · ${{fmt(data.l1_manual_review)}} manual review`,
          highlight: true,
        }},
        {{
          label: "Included",
          title: "Studies included at Level 1",
          count: fmt(data.l1_included),
          sub: data.l1_pending ? `${{fmt(data.l1_pending)}} pending` : "With PDF evidence snippets",
        }},
      ] : [
        {{
          type: "branch",
          main: {{
            label: "Identification",
            title: "Records identified (databases)",
            count: fmt(data.identified),
          }},
          side: {{
            label: "Removed",
            title: "Duplicate records",
            count: fmt(data.duplicates_removed),
          }},
        }},
        {{
          label: "Screening",
          title: "Records screened",
          count: fmt(data.screened),
          sub: "Deduplicated EBSCO pool",
        }},
        {{
          label: "Eligibility",
          title: "Reports assessed for eligibility",
          count: fmt(data.pdfs_downloaded),
          sub: `${{data.pdfs_download_pct ?? 0}}% PDFs downloaded · target ${{fmt(data.full_text_assessed_target ?? data.after_dedup)}}`,
          highlight: true,
        }},
        {{
          label: "Included",
          title: "Studies included in synthesis",
          count: fmt(data.included),
          sub: "Legacy gold standard",
        }},
      ];

      const flow = document.getElementById("prisma-flow");
      const parts = [];
      stages.forEach((stage, idx) => {{
        if (stage.type === "branch") {{
          parts.push(`
            <div class="prisma-stage">
              <div class="prisma-stage-row">
                <div class="prisma-box">
                  <div class="prisma-box-label">${{escHtml(stage.main.label)}}</div>
                  <div class="prisma-box-title">${{escHtml(stage.main.title)}}</div>
                  <div class="prisma-count">${{stage.main.count}}</div>
                </div>
                <div class="prisma-side-box">
                  <div class="prisma-box-label">${{escHtml(stage.side.label)}}</div>
                  <div class="prisma-box-title">${{escHtml(stage.side.title)}}</div>
                  <div class="prisma-count">${{stage.side.count}}</div>
                </div>
              </div>
            </div>`);
        }} else {{
          parts.push(`
            <div class="prisma-stage">
              <div class="prisma-box" style="${{stage.highlight ? "border-color:var(--accent)" : ""}}">
                <div class="prisma-box-label">${{escHtml(stage.label)}}</div>
                <div class="prisma-box-title">${{escHtml(stage.title)}}</div>
                <div class="prisma-count">${{stage.count}}</div>
                ${{stage.sub ? `<div class="prisma-sub">${{escHtml(stage.sub)}}</div>` : ""}}
              </div>
            </div>`);
        }}
        if (idx < stages.length - 1) {{
          parts.push('<div class="prisma-arrow">▼</div>');
        }}
      }});
      flow.innerHTML = parts.join("");

      const legend = document.getElementById("prisma-legend");
      const legendItems = is1150 ? [
        {{ n: data.identified, label: "Export 1–150" }},
        {{ n: data.off_pool_removed, label: "Off-pool removed" }},
        {{ n: data.in_pool, label: "In-pool" }},
        {{ n: data.full_text_assessed, label: "L1 assessed" }},
        {{ n: data.l1_included, label: "L1 included" }},
        {{ n: data.l1_excluded_total, label: "L1 excluded" }},
      ] : [
        {{ n: data.identified, label: "Identified" }},
        {{ n: data.duplicates_removed, label: "Duplicates removed" }},
        {{ n: data.after_dedup, label: "Screen pool" }},
        {{ n: data.pdfs_downloaded, label: "PDFs downloaded (live)" }},
        {{ n: data.fully_coded, label: "Fully coded (live)" }},
        {{ n: data.included, label: "Included (legacy)" }},
      ];
      legend.innerHTML = legendItems.map((item) => `
        <div class="prisma-legend-item">
          <strong>${{fmt(item.n)}}</strong>
          ${{escHtml(item.label)}}
        </div>`).join("");
    }}


    function renderOnHand(data, source) {{
      document.getElementById("on-hand-updated").textContent =
        "Updated " + fmtTime(data.last_updated) + (source ? " · " + source : "");
      const holdout = data.legacy_holdout_n ?? 182;
      document.getElementById("on-hand-holdout-note").innerHTML =
        "<strong>Legacy holdout:</strong> " + holdout + " included studies (" + escHtml(data.legacy_holdout_note || "") + ")";
      const cards = [
        {{ label: "PDFs on hand", value: data.pdf_count, sub: "/ " + data.cohort_n }},
        {{ label: "L1 screened", value: data.l1_screened, sub: "decisions" }},
        {{ label: "Manual review", value: data.l1_manual_review ?? 0, sub: "needs human" }},
        {{ label: "Partially coded", value: data.partially_coded, sub: "extraction pre-fills" }},
      ];
      document.getElementById("on-hand-cards").innerHTML = cards.map((c) =>
        '<div class="card"><div class="card-label">' + escHtml(c.label) + '</div>' +
        '<div class="card-value">' + (c.value ?? 0).toLocaleString() + ' <small>' + escHtml(c.sub) + '</small></div></div>'
      ).join("");
      renderTable("on-hand-l1-table", {{
        included: data.l1_included,
        excluded: data.l1_excluded,
        excluded_pls: data.l1_excluded_pls,
        manual_review: data.l1_manual_review ?? 0,
        pending: data.l1_pending,
      }});
      renderTable("on-hand-exam-table", data.examination_status_counts);
      if (data.cohort_source) {{
        document.getElementById("on-hand-cohort-source").textContent = data.cohort_source;
      }}
      renderOverview();
    }}

    function renderWorklist1150(data, source) {{
      worklistData = data;
      document.getElementById("worklist-updated").textContent =
        "Updated " + fmtTime(data.last_updated) + (source ? " · " + source : "");
      document.getElementById("worklist-definition").textContent = data.definition || "";
      const cards = [
        {{ label: "In-pool total", value: data.worklist_n, sub: "EBSCO 1–150" }},
        {{ label: "Scanned", value: data.scanned, sub: "/ " + data.worklist_n }},
        {{ label: "Included", value: data.included, sub: "L1 pass" }},
        {{ label: "Excluded", value: (data.excluded || 0) + (data.excluded_pls || 0), sub: "fail + PLS" }},
        {{ label: "Manual review", value: data.manual_review, sub: "your queue" }},
        {{ label: "Pending", value: data.pending, sub: "no decision" }},
      ];
      document.getElementById("worklist-cards").innerHTML = cards.map((c) =>
        '<div class="card"><div class="card-label">' + escHtml(c.label) + '</div>' +
        '<div class="card-value">' + (c.value ?? 0).toLocaleString() + ' <small>' + escHtml(c.sub) + '</small></div></div>'
      ).join("");
      const pct = data.scanned_pct ?? 0;
      document.getElementById("worklist-scanned-pct-label").textContent = pct + "%";
      document.getElementById("worklist-scanned-bar").style.width = pct + "%";
      const summaryTables = data.summary_tables || [];
      const summaryContainer = document.getElementById("worklist-summary-sections");
      summaryContainer.innerHTML = summaryTables.length
        ? summaryTables.map(renderSummaryTable).join("")
        : '<p class="summary-note">No summary statistics yet. Re-run the counter after screening updates.</p>';
      if (data.evidence_csv_path) {{
        document.getElementById("worklist-evidence-path").textContent = data.evidence_csv_path;
      }}
      const verification = data.verification_sample || [];
      if (verification.length) {{
        const vrows = verification.map((row) => `
          <tr>
            <td>${{escHtml(row.master_id)}}</td>
            <td class="count">${{escHtml(row.ebsco_search_position)}}</td>
            <td class="title-cell" title="${{escHtml(row.title)}}">${{escHtml(row.title)}}</td>
            <td>${{escHtml(row.decision)}}</td>
            <td>${{escHtml(row.confidence)}}</td>
            <td><code>${{escHtml(row.decision_reason_code)}}</code></td>
            <td class="evidence-cell">${{escHtml(row.decision_reason_text)}}</td>
            <td class="evidence-cell">${{escHtml(row.evidence_snippet)}}</td>
          </tr>`).join("");
        document.getElementById("worklist-verification").innerHTML = `
          <div class="table-scroll">
            <table class="results-table">
              <thead><tr>
                <th>master_id</th><th>EBSCO #</th><th>Title</th><th>Decision</th><th>Conf.</th>
                <th>Reason code</th><th>Reason text</th><th>Evidence</th>
              </tr></thead>
              <tbody>${{vrows}}</tbody>
            </table>
          </div>`;
      }}
      const summary = data.screening_summary_table;
      if (summary && (summary.rows || []).length) {{
        document.getElementById("worklist-evidence-note").textContent = summary.note || "";
        const cols = summary.columns || [];
        const headers = cols.map((c) => `<th>${{escHtml(c)}}</th>`).join("");
        const erows = (summary.rows || []).map((row) => {{
          const cells = cols.map((col) => {{
            const raw = row[col] ?? "";
            const cls = col === "evidence_snippet" || col === "decision_reason_text"
              ? "evidence-cell"
              : (col === "title" ? "title-cell" : "");
            return `<td class="${{cls}}" title="${{escHtml(raw)}}">${{escHtml(raw) || "—"}}</td>`;
          }}).join("");
          return `<tr>${{cells}}</tr>`;
        }}).join("");
        document.getElementById("worklist-evidence-table").innerHTML = `
          <div class="table-scroll">
            <table class="results-table">
              <thead><tr>${{headers}}</tr></thead>
              <tbody>${{erows}}</tbody>
            </table>
          </div>`;
      }}
      renderOverview();
    }}

    function overviewCardsHtml(cards) {{
      return cards.map((c) =>
        '<div class="card"><div class="card-label">' + escHtml(c.label) + '</div>' +
        '<div class="card-value">' + (c.value ?? 0).toLocaleString() + ' <small>' + escHtml(c.sub) + '</small></div></div>'
      ).join("");
    }}

    function renderOverview() {{
      const wl = worklistData || {{}};
      const eb = ebsco150SummaryData || {{}};
      const pool = progressData || {{}};
      const cc = eb.coding_counts || {{}};
      const strands = [
        {{
          title: "EBSCO 1–150 screening",
          tab: "screening-1150",
          cards: [
            {{ label: "In-pool", value: wl.worklist_n, sub: "positions 1–150" }},
            {{ label: "L1 scanned", value: wl.scanned, sub: (wl.scanned_pct ?? 0) + "%" }},
            {{ label: "Included", value: wl.included, sub: "L1 pass" }},
            {{ label: "Manual review", value: wl.manual_review, sub: "queue" }},
          ],
        }},
        {{
          title: "Extraction results (RQ outputs)",
          tab: "results-1150",
          cards: [
            {{ label: "L1 included", value: cc.l1_included, sub: "pass all criteria" }},
            {{ label: "Fully coded", value: cc.fully_coded, sub: "AI extraction" }},
            {{ label: "Partial", value: cc.partial_coded, sub: "included only" }},
          ],
        }},
        {{
          title: "Full 570 pool",
          tab: "progress",
          cards: [
            {{ label: "Downloaded", value: pool.pdf_downloaded, sub: "/ " + (pool.pool_size || 570) }},
            {{ label: "Fully coded", value: pool.exam_fully_coded, sub: "examination" }},
            {{ label: "Remaining", value: pool.remaining_to_examine, sub: "to examine" }},
          ],
        }},
      ];
      document.getElementById("overview-strands").innerHTML = strands.map((s) => `
        <div class="overview-strand">
          <h3>${{escHtml(s.title)}}</h3>
          <div class="cards">${{overviewCardsHtml(s.cards)}}</div>
          <a href="#tab-${{s.tab}}" class="overview-link" data-goto-tab="${{s.tab}}">Open tab →</a>
        </div>`).join("");
    }}

    function renderPrevalenceBars(charts, title) {{
      if (!charts || !charts.length) {{
        return "";
      }}
      const maxPct = Math.max(...charts.map((c) => c.pct || 0), 1);
      const rows = charts.map((item) => `
        <div class="prevalence-row">
          <span class="prevalence-label">${{escHtml(item.label)}}</span>
          <div class="prevalence-bar" title="${{item.count}} / ${{item.total}}">
            <div class="prevalence-bar-fill" style="width:${{Math.max(2, (item.pct / maxPct) * 100)}}%"></div>
          </div>
          <span class="prevalence-pct">${{item.count}} (${{item.pct}}%)</span>
        </div>`).join("");
      return `
        <div class="prevalence-block">
          <h3>${{escHtml(title)}}</h3>
          ${{rows}}
        </div>`;
    }}

    const EBSCO_150_TABLE_GROUPS = [
      {{
        id: "rq-primary",
        heading: "Primary RQ — ULMC implementation & misuse evidence",
        defaultOpen: true,
        tableIds: [
          "corpus_counts", "pls_usage", "harman_deployed",
          "three_step_procedure", "richardson_2009_cited", "journal_ulmc", "model_complexity",
        ],
      }},
      {{
        id: "rq-srq1",
        heading: "Secondary RQ1 — ULMC retention in final models",
        tableIds: ["ulmc_fit_cross"],
      }},
      {{
        id: "rq-srq2",
        heading: "Secondary RQ2 — Procedural remedies alongside ULMC",
        tableIds: ["procedural_remedies"],
      }},
      {{
        id: "rq-srq3",
        heading: "Secondary RQ3 — Method variance % distribution",
        tableIds: ["method_variance_pct", "mv_inference"],
      }},
      {{
        id: "rq-sensitivity",
        heading: "Sensitivity & coding quality",
        tableIds: [
          "publisher_outlet", "business_school_authors", "management_domain",
          "details_in_supplement", "extraction_incomplete_main_text",
        ],
      }},
    ];

    function renderResultsToc() {{
      const toc = document.getElementById("results-toc");
      if (!toc) return;
      const links = [
        {{ href: "#scope-fully-coded", label: "Fully coded cohort" }},
        {{ href: "#scope-l1-included", label: "L1 included cohort" }},
        ...EBSCO_150_TABLE_GROUPS.map((g) => ({{ href: "#" + g.id, label: g.heading.split(" — ")[0] }})),
      ];
      toc.innerHTML = "<strong>Jump to:</strong> " + links.map((l) =>
        `<a href="${{l.href}}" data-scroll="${{l.href.slice(1)}}">${{escHtml(l.label)}}</a>`
      ).join(" · ");
      toc.querySelectorAll("a[data-scroll]").forEach((a) => {{
        a.addEventListener("click", (e) => {{
          e.preventDefault();
          const el = document.getElementById(a.dataset.scroll);
          if (el) el.scrollIntoView({{ behavior: "smooth", block: "start" }});
        }});
      }});
    }}

    function renderGroupedSummaryTables(tables, options) {{
      const collapsible = !options || options.collapsible !== false;
      const byId = {{}};
      (tables || []).forEach((t) => {{ if (t.id) byId[t.id] = t; }});
      const rendered = new Set();
      const parts = [];
      EBSCO_150_TABLE_GROUPS.forEach((group) => {{
        const groupTables = group.tableIds.map((id) => byId[id]).filter(Boolean);
        if (!groupTables.length) return;
        groupTables.forEach((t) => rendered.add(t.id));
        const inner = groupTables.map((t) => renderSummaryTable(t, {{ collapsible }})).join("");
        if (collapsible) {{
          const openAttr = group.defaultOpen ? " open" : "";
          parts.push(`
            <details class="collapsible-rq section-anchor" id="${{group.id}}"${{openAttr}}>
              <summary>${{escHtml(group.heading)}}</summary>
              ${{inner}}
            </details>`);
        }} else {{
          parts.push(`
            <div class="rq-group section-anchor" id="${{group.id}}">
              <h4>${{escHtml(group.heading)}}</h4>
              ${{inner}}
            </div>`);
        }}
      }});
      (tables || []).forEach((t) => {{
        if (t.id && !rendered.has(t.id)) {{
          rendered.add(t.id);
          parts.push(renderSummaryTable(t, {{ collapsible }}));
        }}
      }});
      return parts.join("");
    }}

    function renderMvHistogram(hist) {{
      if (!hist || !(hist.bins || []).length) return "";
      const maxCount = Math.max(...hist.bins.map((b) => b.count || 0), 1);
      const rows = hist.bins.map((bin) => {{
        const h = Math.max(2, ((bin.count || 0) / maxCount) * 100);
        return `
          <div class="histogram-row">
            <span class="prevalence-label">${{escHtml(bin.label)}}</span>
            <div class="histogram-bar-wrap" title="${{bin.count}} studies">
              <div class="histogram-bar" style="height:${{h}}%"></div>
            </div>
            <span class="histogram-count">${{bin.count}}</span>
          </div>`;
      }}).join("");
      const note = hist.n_numeric != null
        ? `<p class="visual-note">n=${{hist.n_numeric}} with numeric method_variance_pct (of ${{hist.total}} fully coded)</p>`
        : "";
      return `
        <div class="prevalence-block">
          <h3>Method variance % distribution</h3>
          ${{note}}
          ${{rows}}
        </div>`;
    }}

    function renderTemporalTrends(trends) {{
      if (!trends || !trends.length) return "";
      const maxCount = Math.max(...trends.map((t) => t.count || 0), 1);
      const rows = trends.map((item) => `
        <div class="prevalence-row">
          <span class="prevalence-label">${{escHtml(String(item.year))}}</span>
          <div class="prevalence-bar" title="${{item.count}} studies">
            <div class="prevalence-bar-fill" style="width:${{Math.max(2, ((item.count || 0) / maxCount) * 100)}}%; background: linear-gradient(90deg, var(--accent), #818cf8)"></div>
          </div>
          <span class="prevalence-pct">${{item.count}}</span>
        </div>`).join("");
      return `
        <div class="prevalence-block">
          <h3>Publication year trend</h3>
          ${{rows}}
        </div>`;
    }}

    function renderScopeVisuals(visuals) {{
      if (!visuals) return "";
      return [
        renderThreeStepChart(visuals.three_step_chart),
        renderMvHistogram(visuals.mv_histogram),
        renderTemporalTrends(visuals.temporal_trends),
      ].join("");
    }}

    function renderThreeStepChart(chart) {{
      return renderPrevalenceBars(chart, "Williams & McGonagle (2016) three-step ULMC compliance");
    }}

    function renderL1Funnel(funnel) {{
      const el = document.getElementById("ebsco-150-l1-funnel");
      if (!funnel || !funnel.length) {{
        el.innerHTML = "";
        return;
      }}
      const maxPct = Math.max(...funnel.map((f) => f.pct || 0), 1);
      const rows = funnel.map((item) => `
        <div class="funnel-row">
          <span class="prevalence-label">${{escHtml(item.label)}}</span>
          <div class="prevalence-bar">
            <div class="funnel-bar-fill" style="width:${{Math.max(2, (item.pct / maxPct) * 100)}}%"></div>
          </div>
          <span class="prevalence-pct">${{item.count}} (${{item.pct}}%)</span>
        </div>`).join("");
      el.innerHTML = `<h3>Level 1 screening funnel</h3>${{rows}}`;
    }}

    function renderEbsco150Summary(data, source) {{
      ebsco150SummaryData = data;
      document.getElementById("ebsco-150-summary-updated").textContent =
        "Updated " + fmtTime(data.last_updated) + (source ? " · " + source : "");
      const cc = data.coding_counts || {{}};
      const codingCards = [
        {{ label: "L1 screened", value: cc.screened, sub: "positions 1–150" }},
        {{ label: "L1 included", value: cc.l1_included, sub: "pass all criteria" }},
        {{ label: "Fully coded (AI)", value: cc.fully_coded, sub: "in 1–150 worklist" }},
        {{ label: "Partial coding", value: cc.partial_coded, sub: "included only" }},
      ];
      document.getElementById("ebsco-150-coding-cards").innerHTML = codingCards.map((c) =>
        '<div class="card"><div class="card-label">' + escHtml(c.label) + '</div>' +
        '<div class="card-value">' + (c.value ?? 0).toLocaleString() + ' <small>' + escHtml(c.sub) + '</small></div></div>'
      ).join("");
      renderL1Funnel(data.l1_funnel || []);
      const scopes = data.scopes || {{}};
      const scopeOrder = ["fully_coded_1_150", "l1_included_coded"];
      const scopeAnchors = {{ fully_coded_1_150: "scope-fully-coded", l1_included_coded: "scope-l1-included" }};
      const parts = scopeOrder.filter((key) => scopes[key]).map((key) => {{
        const scope = scopes[key];
        const summary = scope.summary || {{}};
        const tables = summary.tables || [];
        const tableHtml = renderGroupedSummaryTables(tables, {{ collapsible: true }});
        const anchor = scopeAnchors[key] || ("scope-" + key);
        return `
          <div class="extraction-summary-scope section-anchor" id="${{anchor}}">
            <h3>${{escHtml(scope.label || key)}}</h3>
            <p class="scope-meta">n=${{scope.n ?? 0}} · ${{summary.table_count ?? tables.length}} summary tables</p>
            ${{renderPrevalenceBars(scope.prevalence_charts, "Top prevalence metrics")}}
            ${{renderScopeVisuals(scope.visuals)}}
            ${{tableHtml || '<p class="summary-note">No summary tables for this scope.</p>'}}
          </div>`;
      }});
      document.getElementById("ebsco-150-extraction-summary").innerHTML =
        parts.join("") || '<p class="summary-note">No extraction summary yet. Re-run the counter after coding updates.</p>';
      renderResultsToc();
      renderOverview();
    }}

    function activateTab(tabId) {{
      if (!tabId || !document.getElementById("tab-" + tabId)) return;
      document.querySelectorAll(".tab").forEach((b) => {{
        b.classList.toggle("active", b.dataset.tab === tabId);
      }});
      document.querySelectorAll(".tab-panel").forEach((p) => {{
        p.classList.toggle("active", p.id === "tab-" + tabId);
      }});
      if (location.hash !== "#tab-" + tabId) {{
        history.replaceState(null, "", "#tab-" + tabId);
      }}
    }}

    function setupTabs() {{
      document.querySelectorAll(".tab").forEach((btn) => {{
        btn.addEventListener("click", () => activateTab(btn.dataset.tab));
      }});
      document.querySelectorAll("[data-goto-tab]").forEach((link) => {{
        link.addEventListener("click", (e) => {{
          e.preventDefault();
          activateTab(link.dataset.gotoTab);
        }});
      }});
      const hash = (location.hash || "").replace(/^#tab-/, "");
      if (hash && document.getElementById("tab-" + hash)) {{
        activateTab(hash);
      }}
    }}

    document.getElementById("results-filter").addEventListener("input", (e) => {{
      resultsFilter = e.target.value;
      renderResults(resultsData);
    }});

    async function tryFetch() {{
      let progressOk = false;
      let prismaOk = false;
      let resultsOk = false;
      try {{
        const res = await fetch(JSON_URL + "?t=" + Date.now());
        if (!res.ok) throw new Error("HTTP " + res.status);
        render(await res.json(), "live JSON (auto-refresh every 30s)");
        progressOk = true;
      }} catch (_) {{
        render(EMBEDDED, "embedded snapshot (re-run counter + refresh page)");
      }}
      try {{
        const res = await fetch(PRISMA_URL + "?t=" + Date.now());
        if (!res.ok) throw new Error("HTTP " + res.status);
        renderPrisma(await res.json());
        prismaOk = true;
      }} catch (_) {{
        renderPrisma(PRISMA_EMBEDDED);
      }}
      try {{
        const res = await fetch(RESULTS_URL + "?t=" + Date.now());
        if (!res.ok) throw new Error("HTTP " + res.status);
        renderResults(await res.json());
        resultsOk = true;
      }} catch (_) {{
        renderResults(RESULTS_EMBEDDED);
      }}
      try {{
        const res = await fetch(ON_HAND_URL + "?t=" + Date.now());
        if (!res.ok) throw new Error("HTTP " + res.status);
        renderOnHand(await res.json(), "live JSON");
      }} catch (_) {{
        renderOnHand(ON_HAND_EMBEDDED, "embedded snapshot");
      }}
      try {{
        const res = await fetch(WORKLIST_URL + "?t=" + Date.now());
        if (!res.ok) throw new Error("HTTP " + res.status);
        renderWorklist1150(await res.json(), "live JSON");
      }} catch (_) {{
        renderWorklist1150(WORKLIST_EMBEDDED, "embedded snapshot");
      }}
      try {{
        const res = await fetch(EBSCO_150_SUMMARY_URL + "?t=" + Date.now());
        if (!res.ok) throw new Error("HTTP " + res.status);
        renderEbsco150Summary(await res.json(), "live JSON");
      }} catch (_) {{
        renderEbsco150Summary(EBSCO_150_SUMMARY_EMBEDDED, "embedded snapshot");
      }}
      return progressOk && prismaOk && resultsOk;
    }}

    setupTabs();
    renderPrisma(PRISMA_EMBEDDED);
    renderResults(RESULTS_EMBEDDED);
    renderOnHand(ON_HAND_EMBEDDED, "embedded snapshot");
    renderWorklist1150(WORKLIST_EMBEDDED, "embedded snapshot");
    renderEbsco150Summary(EBSCO_150_SUMMARY_EMBEDDED, "embedded snapshot");
    render(EMBEDDED, "embedded snapshot");
    renderOverview();
    tryFetch();
    setInterval(tryFetch, REFRESH_MS);
  </script>
</body>
</html>
"""

