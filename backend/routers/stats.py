"""
Stats Router — serves cached evaluation results and triggers re-evaluation.
"""

import os
import json
import threading
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks

router = APIRouter()

BACKEND_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_PATH    = os.path.join(BACKEND_DIR, "results", "evaluation_results.json")
_eval_running   = False


def _run_evaluation():
    global _eval_running
    try:
        import sys
        nlp_utils = os.path.join(BACKEND_DIR, "scripts", "nlp_utils")
        if nlp_utils not in sys.path:
            sys.path.insert(0, nlp_utils)
        import subprocess
        subprocess.run(
            ["python", os.path.join(nlp_utils, "evaluate_pipeline.py")],
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    finally:
        _eval_running = False


@router.get("/stats")
def get_stats():
    """Return cached evaluation results."""
    if not os.path.exists(RESULTS_PATH):
        raise HTTPException(
            status_code=404,
            detail="No evaluation results found. POST /api/stats/evaluate to run evaluation."
        )
    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["is_running"] = _eval_running
    return data


@router.post("/stats/evaluate")
def trigger_evaluation(background_tasks: BackgroundTasks):
    """Trigger a fresh evaluation in the background."""
    global _eval_running
    if _eval_running:
        return {"status": "already_running", "message": "Evaluation is already in progress."}
    _eval_running = True
    background_tasks.add_task(_run_evaluation)
    return {"status": "started", "message": "Evaluation started. Poll GET /api/stats for results."}
