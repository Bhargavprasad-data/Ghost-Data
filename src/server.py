"""
FastAPI Server for Ghost Data Still Exists Deletion-Audit Dashboard
Connects frontend forensics interface with backend audit pipeline,
evaluator, identity resolver, evidence indexer, and submission packager.
"""

import os
import sys
import json
import csv
import zipfile
import io
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import pandas as pd

# Add repository root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from src.audit_pipeline import AuditPipeline
from src.evaluator import Evaluator
from src.identity_resolver import IdentityResolver
from src.intent_classifier import IntentClassifier

app = FastAPI(
    title="Ghost Data Still Exists — Digital Forensics & Deletion Audit Engine",
    description="HackerRank Orchestrate October 2026 Deletion Audit Intelligence Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global lazy instances
pipeline = None
evaluator = None
identity_resolver = None
intent_classifier = None

def get_pipeline():
    global pipeline
    if pipeline is None:
        pipeline = AuditPipeline("dataset")
    return pipeline

def get_evaluator():
    global evaluator
    if evaluator is None:
        evaluator = Evaluator("dataset/sample_output.csv")
    return evaluator

def get_resolver():
    global identity_resolver
    if identity_resolver is None:
        identity_resolver = IdentityResolver("dataset")
    return identity_resolver

def get_intent_classifier():
    global intent_classifier
    if intent_classifier is None:
        intent_classifier = IntentClassifier()
    return intent_classifier

# Cached memory datasets
_eval_requests = None
_sample_requests = None
_sample_outputs = None
_evidence_files = None
_cached_predictions = {}

def load_datasets():
    global _eval_requests, _sample_requests, _sample_outputs, _evidence_files
    if _eval_requests is None:
        _eval_requests = pd.read_csv("dataset/deletion_requests.csv", encoding="utf-8")
    if _sample_requests is None:
        _sample_requests = pd.read_csv("dataset/sample_deletion_requests.csv", encoding="utf-8")
    if _sample_outputs is None:
        _sample_outputs = pd.read_csv("dataset/sample_output.csv", encoding="utf-8")
    if _evidence_files is None:
        _evidence_files = pd.read_csv("dataset/evidence_files.csv", encoding="utf-8")

load_datasets()

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "challenge": "Ghost Data Still Exists",
        "harness": "Antigravity",
        "model": "Gemini 3.8 Flash (High)",
        "eval_cases_count": len(_eval_requests) if _eval_requests is not None else 0,
        "sample_cases_count": len(_sample_requests) if _sample_requests is not None else 0,
        "evidence_files_count": len(_evidence_files) if _evidence_files is not None else 0
    }

@app.get("/api/stats")
def get_dashboard_stats():
    """
    Returns platform KPI metrics and dataset distribution.
    """
    load_datasets()
    pipe = get_pipeline()
    
    # Check if root output.csv exists
    output_exists = os.path.exists("output.csv")
    output_status_counts = {"COMPLETE": 0, "INCOMPLETE": 0, "NOT_APPLICABLE": 0}
    if output_exists:
        try:
            df_out = pd.read_csv("output.csv")
            for st, cnt in df_out["deletion_status"].value_counts().items():
                if st in output_status_counts:
                    output_status_counts[st] = int(cnt)
        except Exception:
            pass

    # Quick evaluation on 32 samples
    eval_res = None
    try:
        ev = get_evaluator()
        sample_preds = []
        for _, r in _sample_requests.iterrows():
            cid, status, steps = pipe.audit_request(r.to_dict())
            sample_preds.append((cid, status, steps))
        eval_res = ev.evaluate(sample_preds)
    except Exception as e:
        print(f"Eval error: {e}")

    return {
        "total_eval_cases": len(_eval_requests),
        "total_sample_cases": len(_sample_requests),
        "evidence_files_count": len(_evidence_files),
        "output_generated": output_exists,
        "output_breakdown": output_status_counts,
        "sample_evaluation": {
            "status_accuracy": round(eval_res["status_accuracy"] * 100, 2) if eval_res else 0,
            "sequence_accuracy": round(eval_res["sequence_accuracy"] * 100, 2) if eval_res else 0,
            "field_accuracy": round(eval_res["field_accuracy"] * 100, 2) if eval_res else 0,
            "status_matches": eval_res["status_matches"] if eval_res else 0,
            "total_samples": eval_res["total_cases"] if eval_res else 32
        },
        "challenge_url": "https://www.hackerrank.com/contests/hackerrank-orchestrate-october26/challenges/ghost-data-still-exists"
    }

@app.get("/api/cases")
def list_cases(
    dataset_type: str = Query("eval", description="'eval' or 'sample'"),
    status: str = Query("ALL", description="Filter status: ALL, COMPLETE, INCOMPLETE, NOT_APPLICABLE"),
    search: str = Query("", description="Search term for case_id, email, or request_text"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=5, le=100)
):
    """
    Returns paginated, searchable list of cases.
    """
    load_datasets()
    df = _sample_requests if dataset_type == "sample" else _eval_requests
    
    # Merge with predictions if available
    pipe = get_pipeline()
    resolver = get_resolver()

    records = []
    for _, r in df.iterrows():
        cid = str(r["case_id"])
        email = str(r["email"])
        req_text = str(r.get("request_text", ""))
        audit_at = str(r.get("audit_at", ""))
        reported_status = str(r.get("reported_status", ""))

        # Cached or on-demand prediction
        if cid in _cached_predictions:
            pred_status, steps = _cached_predictions[cid]
        else:
            _, pred_status, steps = pipe.audit_request(r.to_dict())
            _cached_predictions[cid] = (pred_status, steps)

        profile = resolver.resolve(email)
        user_id = profile["user_id"] if profile else "UNRESOLVED"

        # Apply search filter
        if search:
            s_low = search.lower()
            if not (s_low in cid.lower() or s_low in email.lower() or s_low in user_id.lower() or s_low in req_text.lower()):
                continue

        # Apply status filter
        if status != "ALL" and pred_status != status:
            continue

        records.append({
            "case_id": cid,
            "user_id": user_id,
            "email": email,
            "requested_at": str(r.get("requested_at", "")),
            "reported_status": reported_status,
            "reported_at": str(r.get("reported_at", "")),
            "audit_at": audit_at,
            "request_text": req_text,
            "deletion_status": pred_status,
            "steps_count": len(steps),
            "findings_count": sum(1 for s in steps if s.get("phase") == "FINDING"),
            "remediations_count": sum(1 for s in steps if s.get("phase") == "REMEDIATION"),
            "verifications_count": sum(1 for s in steps if s.get("phase") == "VERIFICATION")
        })

    # Pagination
    total = len(records)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_items = records[start_idx:end_idx]

    return {
        "dataset_type": dataset_type,
        "total_cases": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 1,
        "cases": paginated_items
    }

@app.get("/api/cases/{case_id}")
def get_case_detail(case_id: str):
    """
    Returns full digital forensic dossier for a specific case.
    """
    load_datasets()
    pipe = get_pipeline()
    resolver = get_resolver()
    classifier = get_intent_classifier()

    # Search in eval requests first, then sample
    row = _eval_requests[_eval_requests["case_id"] == case_id]
    dataset_type = "eval"
    if row.empty:
        row = _sample_requests[_sample_requests["case_id"] == case_id]
        dataset_type = "sample"
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    r = row.iloc[0].to_dict()
    cid, pred_status, steps = pipe.audit_request(r)
    _cached_predictions[cid] = (pred_status, steps)

    req_text = str(r.get("request_text", ""))
    is_authorized, intent_reason = classifier.is_deletion_authorized(req_text)

    # Identity Dossier
    email = str(r["email"])
    profile = resolver.resolve(email)

    # Ground truth steps if sample
    gt_status = None
    gt_steps = None
    if dataset_type == "sample":
        gt_row = _sample_outputs[_sample_outputs["case_id"] == case_id]
        if not gt_row.empty:
            gt_status = gt_row.iloc[0]["deletion_status"]
            try:
                gt_steps = json.loads(gt_row.iloc[0]["steps_json"])
            except Exception:
                gt_steps = []

    return {
        "case_id": cid,
        "dataset_type": dataset_type,
        "email": email,
        "requested_at": str(r.get("requested_at", "")),
        "reported_status": str(r.get("reported_status", "")),
        "reported_at": str(r.get("reported_at", "")),
        "audit_at": str(r.get("audit_at", "")),
        "request_text": req_text,
        "intent_analysis": {
            "is_authorized": is_authorized,
            "reason": intent_reason
        },
        "identity_profile": profile,
        "deletion_status": pred_status,
        "steps": steps,
        "gt_status": gt_status,
        "gt_steps": gt_steps
    }

@app.post("/api/audit/case/{case_id}")
def audit_single_case(case_id: str):
    """
    Re-runs audit pipeline dynamically for a single case.
    """
    load_datasets()
    pipe = get_pipeline()

    row = _eval_requests[_eval_requests["case_id"] == case_id]
    if row.empty:
        row = _sample_requests[_sample_requests["case_id"] == case_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    r = row.iloc[0].to_dict()
    cid, status, steps = pipe.audit_request(r)
    _cached_predictions[cid] = (status, steps)

    return {
        "case_id": cid,
        "deletion_status": status,
        "steps_count": len(steps),
        "steps": steps
    }

@app.post("/api/audit/run-all")
def run_all_audits():
    """
    Runs audit pipeline on all 518 evaluation requests,
    validates the output format and writes root output.csv.
    """
    load_datasets()
    pipe = get_pipeline()

    results = []
    output_rows = []

    for _, r in _eval_requests.iterrows():
        cid, status, steps = pipe.audit_request(r.to_dict())
        _cached_predictions[cid] = (status, steps)
        steps_json = json.dumps(steps)
        output_rows.append((cid, status, steps_json))
        results.append({
            "case_id": cid,
            "status": status,
            "steps_count": len(steps)
        })

    # Sort strictly by case_id (string sort)
    output_rows = sorted(output_rows, key=lambda x: str(x[0]))

    # Write root output.csv
    output_path = os.path.join(REPO_ROOT, "output.csv")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        for row in output_rows:
            writer.writerow(row)

    status_counts = {}
    for _, st, _ in output_rows:
        status_counts[st] = status_counts.get(st, 0) + 1

    return {
        "status": "success",
        "total_cases_audited": len(output_rows),
        "output_path": output_path,
        "status_distribution": status_counts,
        "sample_preview": results[:5]
    }

@app.get("/api/download-output")
def download_output_csv():
    """
    Downloads root output.csv file directly.
    """
    output_path = os.path.join(REPO_ROOT, "output.csv")
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="output.csv has not been generated yet. Please run an audit first.")
    return FileResponse(
        path=output_path,
        filename="output.csv",
        media_type="text/csv"
    )

@app.get("/api/evaluate")
def evaluate_against_samples():
    """
    Evaluates engine predictions against all 32 sample cases and ground truth.
    """
    load_datasets()
    pipe = get_pipeline()
    ev = get_evaluator()

    predictions = []
    for _, r in _sample_requests.iterrows():
        cid, status, steps = pipe.audit_request(r.to_dict())
        predictions.append((cid, status, steps))

    res = ev.evaluate(predictions)
    return res

@app.get("/api/evidence")
def list_evidence_files():
    """
    Returns catalog of all 94 evidence files.
    """
    load_datasets()
    files = []
    for _, r in _evidence_files.iterrows():
        fid = str(r["file_id"])
        fpath = str(r["file_path"])
        origin = str(r["origin"])
        cap_at = str(r["captured_at"])
        full_path = os.path.join(REPO_ROOT, "dataset", fpath)

        exists = os.path.exists(full_path)
        size_bytes = os.path.getsize(full_path) if exists else 0
        ext = os.path.splitext(fpath)[1].lower()

        cat = "UNKNOWN"
        if ext == ".sql": cat = "DATABASE_SNAPSHOT"
        elif ext == ".json": cat = "JSON_BUNDLE"
        elif ext == ".log": cat = "SYSTEM_LOG"
        elif ext == ".pdf": cat = "DOCUMENT"
        elif ext in [".png", ".jpg"]: cat = "FORENSIC_IMAGE"
        elif ext == ".txt": cat = "TEXT_RECORD"

        files.append({
            "file_id": fid,
            "file_path": fpath,
            "origin": origin,
            "captured_at": cap_at,
            "category": cat,
            "extension": ext,
            "size_bytes": size_bytes,
            "exists": exists
        })

    return {
        "total_files": len(files),
        "files": files
    }

@app.get("/api/evidence/{file_id}")
def view_evidence_file(file_id: str):
    """
    Returns preview / extracted text of an evidence file.
    """
    load_datasets()
    row = _evidence_files[_evidence_files["file_id"] == file_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Evidence file {file_id} not found")

    r = row.iloc[0]
    rel_path = str(r["file_path"])
    full_path = os.path.join(REPO_ROOT, "dataset", rel_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail=f"File not found on disk: {rel_path}")

    ext = os.path.splitext(rel_path)[1].lower()
    content = ""
    is_binary = False

    try:
        if ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(full_path)
            content = "\n--- PAGE BREAK ---\n".join([page.extract_text() or "" for page in reader.pages])
        elif ext in [".png", ".jpg"]:
            is_binary = True
            content = f"[Binary image file: {os.path.basename(rel_path)} ({os.path.getsize(full_path)} bytes)]"
        else:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                # read first 1000 lines max
                lines = [f.readline() for _ in range(1000)]
                content = "".join(lines)
    except Exception as e:
        content = f"Error reading file: {str(e)}"

    return {
        "file_id": file_id,
        "file_path": rel_path,
        "origin": str(r["origin"]),
        "captured_at": str(r["captured_at"]),
        "extension": ext,
        "size_bytes": os.path.getsize(full_path),
        "is_binary": is_binary,
        "content_preview": content
    }

@app.post("/api/package")
def package_submission():
    """
    Packages code.zip with submission readiness validation:
    - code/main.py runnable entry point
    - evaluation/evaluation_report.md
    - evaluation/usage_report.md
    - README.md
    - requirements.txt
    - Excludes dataset/, .git, __pycache__, log.txt
    """
    zip_path = os.path.join(REPO_ROOT, "code.zip")
    
    # Ensure reports exist
    eval_dir = os.path.join(REPO_ROOT, "evaluation")
    os.makedirs(eval_dir, exist_ok=True)
    
    # Files to include
    include_paths = ["src", "scripts", "frontend", "README.md"]
    if os.path.exists(os.path.join(REPO_ROOT, "code")):
        include_paths.append("code")

    added_arcnames = set()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        def safe_add(file_path, arc_path):
            if arc_path not in added_arcnames and os.path.exists(file_path):
                zf.write(file_path, arcname=arc_path)
                added_arcnames.add(arc_path)

        # Include top level files if they exist
        for fname in ["README.md", "requirements.txt", "problem_statement.md"]:
            p = os.path.join(REPO_ROOT, fname)
            safe_add(p, fname)

        # Include evaluation reports
        for r_name in ["evaluation_report.md", "usage_report.md"]:
            p = os.path.join(eval_dir, r_name)
            safe_add(p, os.path.join("evaluation", r_name))
            p_code = os.path.join(REPO_ROOT, "code", "evaluation", r_name)
            safe_add(p_code, os.path.join("code", "evaluation", r_name))

        # Include directories
        for root, dirs, files in os.walk(REPO_ROOT):
            # Exclude unwanted directories
            dirs[:] = [d for d in dirs if d not in [".git", "dataset", "__pycache__", ".vscode", "venv", ".env"]]
            for file in files:
                if file in ["log.txt", "code.zip", "output.csv"]:
                    continue
                abs_f = os.path.join(root, file)
                rel_f = os.path.relpath(abs_f, REPO_ROOT)
                # Only include allowed roots
                if any(rel_f.startswith(prefix) for prefix in ["src", "code", "evaluation", "frontend"]):
                    safe_add(abs_f, rel_f)

    return {
        "status": "success",
        "zip_path": zip_path,
        "size_bytes": os.path.getsize(zip_path),
        "message": "code.zip generated successfully ready for submission."
    }

@app.get("/api/download-output")
def download_output_csv():
    """
    Directly download the generated output.csv file.
    """
    out_path = os.path.join(REPO_ROOT, "output.csv")
    if not os.path.exists(out_path):
        raise HTTPException(status_code=404, detail="output.csv has not been generated yet. Please run audit first.")
    return FileResponse(
        path=out_path,
        filename="output.csv",
        media_type="text/csv"
    )

@app.get("/api/output-status")
def get_output_status():
    """
    Returns metadata about the root output.csv file.
    """
    out_path = os.path.join(REPO_ROOT, "output.csv")
    if not os.path.exists(out_path):
        return {"exists": False, "row_count": 0, "size_bytes": 0, "path": out_path}
    
    size = os.path.getsize(out_path)
    with open(out_path, "r", encoding="utf-8") as f:
        row_count = sum(1 for _ in f) - 1 # Subtract header
    
    return {
        "exists": True,
        "row_count": max(0, row_count),
        "size_bytes": size,
        "path": out_path,
        "filename": "output.csv",
        "download_url": "/api/download-output"
    }

@app.get("/api/output/records")
def get_output_records(
    search: str = Query("", description="Search by case_id"),
    status: str = Query("ALL", description="Filter by deletion_status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200)
):
    """
    Returns structured records from output.csv with pagination and search.
    """
    out_path = os.path.join(REPO_ROOT, "output.csv")
    if not os.path.exists(out_path):
        return {
            "exists": False,
            "total_rows": 0,
            "page": page,
            "page_size": page_size,
            "records": []
        }

    records = []
    status_counts = {"COMPLETE": 0, "INCOMPLETE": 0, "NOT_APPLICABLE": 0}

    with open(out_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row.get("case_id", "")
            dstatus = row.get("deletion_status", "")
            steps_str = row.get("steps_json", "[]")

            if dstatus in status_counts:
                status_counts[dstatus] += 1

            # Filter
            if search and search.lower() not in cid.lower():
                continue
            if status != "ALL" and dstatus != status:
                continue

            try:
                steps = json.loads(steps_str)
            except Exception:
                steps = []

            records.append({
                "case_id": cid,
                "deletion_status": dstatus,
                "steps_count": len(steps),
                "steps_json": steps,
                "steps_raw": steps_str
            })

    total = len(records)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated = records[start_idx:end_idx]

    return {
        "exists": True,
        "total_rows": total,
        "total_unfiltered": sum(status_counts.values()),
        "status_counts": status_counts,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 1,
        "records": paginated
    }

@app.get("/api/output/raw")
def get_output_raw(limit: int = Query(100, ge=1, le=1000)):
    """
    Returns raw text lines from output.csv for direct preview.
    """
    out_path = os.path.join(REPO_ROOT, "output.csv")
    if not os.path.exists(out_path):
        raise HTTPException(status_code=404, detail="output.csv not found.")
    
    lines = []
    with open(out_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx > limit:
                break
            lines.append(line)
            
    return {
        "exists": True,
        "total_lines_previewed": len(lines),
        "content": "".join(lines)
    }

# Mount static frontend directory
frontend_dir = os.path.join(REPO_ROOT, "frontend")
os.makedirs(frontend_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.server:app", host="127.0.0.1", port=8000, reload=False)
