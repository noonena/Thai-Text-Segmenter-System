"""
Stats Router — combines results from trainer JSON files + word_seg evaluation.
"""

import os
import json
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from utils.database import require_auth

router = APIRouter()

BACKEND_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR   = os.path.join(BACKEND_DIR, "results")
_eval_running = False


def _load_json(filename: str):
    path = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _run_evaluation():
    global _eval_running
    try:
        import sys, subprocess
        nlp_utils = os.path.join(BACKEND_DIR, "scripts", "nlp_utils")
        if nlp_utils not in sys.path:
            sys.path.insert(0, nlp_utils)
        subprocess.run(
            ["python", os.path.join(nlp_utils, "evaluate_pipeline.py")],
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    finally:
        _eval_running = False


@router.get("")
def get_stats(_user: dict = Depends(require_auth)):
    mtu  = _load_json("mtu_results.json")
    syl  = _load_json("syllable_results.json")
    word = _load_json("word_seg_results.json")
    pos  = _load_json("pos_results.json")

    if not any([mtu, syl, word, pos]):
        raise HTTPException(
            status_code=404,
            detail="No results found. Train models or POST /api/statistics/evaluate to run word seg evaluation."
        )

    stages = []
    if mtu:  stages.append(("MTU",      mtu.get("f1", 0)))
    if syl:  stages.append(("Syllable", syl.get("f1", 0)))
    if word: stages.append(("Word seg", word.get("f1", 0)))
    if pos:  stages.append(("POS",      pos.get("accuracy", 0)))
    weakest = min(stages, key=lambda x: x[1])[0] if stages else "N/A"

    timestamps = [d["timestamp"] for d in [mtu, syl, word, pos] if d and "timestamp" in d]
    timestamp = max(timestamps) if timestamps else ""

    sentences_evaluated = (word or {}).get("sentences_evaluated") or \
                          (mtu or {}).get("sentences_evaluated") or 0

    return {
        "timestamp": timestamp,
        "sentences_evaluated": sentences_evaluated,
        "mtu": {
            "label_accuracy": mtu["label_accuracy"],
            "precision":      mtu["precision"],
            "recall":         mtu["recall"],
            "f1":             mtu["f1"],
        } if mtu else None,
        "syllable": {
            "precision": syl["precision"],
            "recall":    syl["recall"],
            "f1":        syl["f1"],
        } if syl else None,
        "word_seg": {
            "precision": word["precision"],
            "recall":    word["recall"],
            "f1":        word["f1"],
            "errors":    word.get("errors", []),
        } if word else None,
        "pos": {
            "accuracy":   pos["accuracy"],
            "total_tags": pos["total_tags"],
            "per_tag":    pos["per_tag"],
        } if pos else None,
        "weakest_stage": weakest,
        "is_running": _eval_running,
    }


@router.post("/evaluate")
def trigger_evaluation(background_tasks: BackgroundTasks, _user: dict = Depends(require_auth)):
    """Trigger word segmentation evaluation in the background."""
    global _eval_running
    if _eval_running:
        return {"status": "already_running", "message": "Evaluation is already in progress."}
    _eval_running = True
    background_tasks.add_task(_run_evaluation)
    return {"status": "started", "message": "Word seg evaluation started. Poll GET /api/statistics for results."}
