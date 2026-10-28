# Ghost Data Still Exists — Autonomous Deletion-Audit Agent

**HackerRank Orchestrate (October 2026)**  
*An enterprise-grade digital forensics engine and interactive forensics dashboard for auditing deletion workflows, detecting ghost records, and producing verifiable remediation plans.*

---
 
## 1. Executive Summary
 
Deletion workflows frequently report **Complete** while personal data persists in secondary replicas, logs, customer support tickets, exports, search indexes, or backups. Moreover, active synchronization and restore pipelines can recreate data that was deleted from its original primary store.

This repository implements the **Ghost Data Still Exists Deletion-Audit Agent**, an autonomous digital-forensics system that:
1. **Verifies Request Intent**: Disregards reported status claims and analyzes `request_text` across multiple languages (English, Spanish, French, Portuguese, Korean, Japanese). Differentiates genuine deletion requests from non-deletion requests (access, export, marketing opt-out, invoice receipts), classifying non-deletion requests as `NOT_APPLICABLE` with `steps_json=[]`.
2. **Reconstructs Identity Graphs**: Traces current identifiers (`user_identities.csv`) and historical changes (`user_audit_log.csv`) including past emails, phone numbers, and SHA256 email hashes to uncover orphaned or stale records.
3. **Discovers Point-in-Time Evidence**: Scans 94 diverse evidence artifacts (SQLite database snapshots, regional/failover SQL replicas, structured JSON exports, server logs, PDF attachments, and application screenshots) strictly up to each case's `audit_at` cutoff time.
4. **Enforces Deletion Policy**: Applies `deletion_rules.csv` across all data categories (`ACCOUNT_TOMBSTONE`, `PROFILE`, `TRANSACTION`, `INTERACTION`, `CONSENT`, `TELEMETRY`), properly preserving account tombstones while redacting prohibited direct PII.
5. **Generates Topological Remediation Plans**: Produces ordered, dependency-safe remediation plans (`FINDING` &rarr; `REMEDIATION` &rarr; `VERIFICATION`) where active data flows and restore risks are blocked before dependent records are removed.

---

## 2. System Architecture

```
OST/
├── code/
│   ├── main.py                     # Official runnable CLI entry point
│   └── evaluation/                 # Bundled evaluation & token usage reports
├── src/
│   ├── audit_pipeline.py           # Core orchestrator coordinating forensic audit flow
│   ├── identity_resolver.py        # Current & historical user identity graph builder
│   ├── intent_classifier.py        # Multilingual deletion authorization classifier
│   ├── evidence_indexer.py         # Multi-format point-in-time evidence parser (SQL, JSON, logs)
│   ├── policy_engine.py            # Deletion rule evaluator & PII redaction matcher
│   ├── remediation_planner.py      # Dependency-safe remediation & verification sequencer
│   ├── evaluator.py                # Ground-truth accuracy benchmarker on sample cases
│   └── server.py                   # FastAPI backend with REST endpoints & static hosting
├── frontend/                       # Enterprise Forensics Console (Hotstar sidebar + Shimmer Skeletons)
│   ├── index.html                  # Dashboard HTML shell
│   ├── app.js                      # UI controllers, modal managers, & API connectors
│   ├── app.css                     # Postman/Linear dark theme & micro-animations
│   └── dist/                       # Vite production bundle
├── dataset/                        # Challenge dataset (read-only input files & evidence)
├── evaluation/
│   ├── evaluation_report.md        # Accuracy, metrics, edge cases, & failures analysis
│   └── usage_report.md             # Token usage, API calls, and cost accounting
├── output.csv                      # Generated predictions (518 evaluation requests)
├── log.txt                         # Chat transcript conforming strictly to AGENTS.md §5.2
└── code.zip                        # Self-contained submission archive
```

---

## 3. Quick Start & Execution

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend development/builds)

### Setup
```bash
# Clone the repository
git clone https://github.com/interviewstreet/hackerrank-orchestrate-october26.git
cd hackerrank-orchestrate-october26

# Install Python dependencies
pip install -r requirements.txt
```

### Option A: Run Full CLI Audit (Generates `output.csv`)
To run the automated deletion-audit pipeline across all 518 evaluation cases and generate the root `output.csv`:

```bash
python code/main.py
```

Output:
```text
============================================================
GHOST DATA STILL EXISTS — DELETION-AUDIT AGENT
============================================================
Loading deletion requests from dataset/deletion_requests.csv...
Loaded 518 requests.
Running audit pipeline on all requests...
Writing 518 rows to C:\Users\Bharg\OneDrive\Desktop\OST\output.csv...
Audit Complete! Status breakdown:
  INCOMPLETE:     313
  COMPLETE:       195
  NOT_APPLICABLE: 10
```

### Option B: Launch Full-Stack Enterprise Forensics Console
To explore cases, inspect evidence, view dossiers, and trigger live audits visually:

```bash
# Start the FastAPI + Static server on port 8000
python -m uvicorn src.server:app --host 127.0.0.1 --port 8000
```
Then open your browser to **`http://127.0.0.1:8000`**.

---

## 4. Web Application Features

The interactive dashboard is designed with a Postman/Linear dark slate aesthetic and JioCinema/Hotstar layout behavior:

* **Hotstar-Style Rail Sidebar**: Fixed 68px anchor rail that never shifts content on desktop; smoothly expands to 260px on hover with Lucide SVG icons.
* **Continuous Shimmer Skeletons**: Real-time heartbeat monitors API health, rendering smooth skeleton cards and tables whenever data is loading or disconnected.
* **Live Case Explorer**: Browse, paginate, search, and filter all 518 evaluation requests and 32 sample cases.
* **Digital Forensic Dossier Drawer**: Inspect individual subjects, historical identity changes, reported claims vs actual findings, and synthesized remediation plans.
* **Live `output.csv` Viewer Modal**:
  * **Table View**: Live search by `case_id`, filter by status (`COMPLETE`, `INCOMPLETE`, `NOT_APPLICABLE`), and view inline `steps_json` snippets.
  * **Raw CSV View**: Preview exact CSV formatted lines and copy raw CSV content with 1-click clipboard integration.
  * **Direct Download**: One-click download button in the topbar header and Output Contract card.
* **Sample Benchmark Tab**: Real-time accuracy metrics and mismatch inspector against the 32 public ground-truth cases.
* **Evidence Catalog**: Inspect SQL snapshots, replicas, JSON blobs, logs, and support PDFs with syntax-highlighted code viewers.

---

## 5. Output Contract & Validation

The solution writes `output.csv` strictly following the challenge contract:

* **File Location**: Repository root (`./output.csv`)
* **Header**: Exactly `case_id,deletion_status,steps_json`
* **Row Count**: Exactly 518 data rows (`case_33` through `case_550`), sorted by `case_id` string order.
* **Allowed Statuses**: `COMPLETE`, `INCOMPLETE`, `NOT_APPLICABLE` (with `steps_json=[]` for non-deletion intents).
* **Phases & Steps Ordering**:
  1. `FINDING`: `REPORT_REMAINING_RECORD`, `REPORT_EXPOSED_PII`, `REPORT_ACTIVE_DATA_FLOW`, `REPORT_RESTORE_RISK` (with valid `evidence_id`).
  2. `REMEDIATION`: `DISABLE_DATA_FLOW`, `BLOCK_RESTORE`, `DELETE_RECORD`, `REDACT_RECORD`, `ANONYMIZE_RECORD` (`evidence_id=""`).
  3. `VERIFICATION`: `VERIFY_RECORD_ABSENT`, `VERIFY_RECORD_PRESENT`, `VERIFY_RECORD_REDACTED`, `VERIFY_RECORD_ANONYMIZED`, `VERIFY_DATA_FLOW_DISABLED`, `VERIFY_RESTORE_BLOCKED`.

---

## 6. Evaluation Reports & Usage

As specified in `AGENTS.md` §6.8, comprehensive reports are documented under `evaluation/` and mirrored in `code/evaluation/`:

1. **[`evaluation/evaluation_report.md`](./evaluation/evaluation_report.md)**:
   - Case-level deletion-status accuracy (68.75% status match on 32 public sample cases).
   - Step-level and field-level concordance analysis.
   - Three custom evaluation cases testing multilingual intent, asynchronous sync drift, and backup restore blockers.
   - Root-cause failure analysis and engineering improvements.
2. **[`evaluation/usage_report.md`](./evaluation/usage_report.md)**:
   - Model Provider: Google DeepMind / Google Cloud AI.
   - Runtime Model: `Gemini 3.8 Flash (High)`.
   - Total Calls: 518 LLM calls across 518 evaluation requests.
   - Input Tokens: 714,840 | Output Tokens: 145,040 | Total Tokens: 859,880.
   - Total Cost: **$0.0971 USD** (~$0.000187 per request).

---

## 7. Chat Transcript Logging

All developer and agent interactions are logged in [`log.txt`](./log.txt) in the repository root adhering strictly to `AGENTS.md` §5.1 and §5.2:
- Mandatory tool identifier: `tool=Antigravity`
- Authoritative runtime model: `model=Gemini 3.8 Flash (High)`
- ISO-8601 timestamps, verbatim prompts, 2-5 sentence summaries, and real execution actions.
- Secrets and real personal data are strictly redacted.

---

## 8. Packaging `code.zip` for Submission

The submission archive `code.zip` can be generated directly via:

```bash
python -c "from src.server import package_submission; print(package_submission())"
```

This packages `code/main.py`, `src/`, `scripts/`, `frontend/`, `README.md`, `requirements.txt`, and `evaluation/` reports while strictly excluding `dataset/`, `.git`, `.venv`, and temporary caches.

Official submission URL:
[https://www.hackerrank.com/contests/hackerrank-orchestrate-october26/challenges/ghost-data-still-exists](https://www.hackerrank.com/contests/hackerrank-orchestrate-october26/challenges/ghost-data-still-exists)
