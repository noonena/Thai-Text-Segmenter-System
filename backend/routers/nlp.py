"""
API Router for Thai Text Processing
Uses complete_pipeline.py from backend/scripts/nlp_utils/
"""

import os
import sys
import json

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import re
from utils.database import require_auth

# =====================================================
# Setup paths for NLP pipeline
# =====================================================
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NLP_UTILS_DIR = os.path.join(BACKEND_DIR, "scripts", "nlp_utils")
_trainers = os.path.join(BACKEND_DIR, "scripts", "trainers")

for _p in [NLP_UTILS_DIR, _trainers, os.path.join(_trainers, "models")]:
    if _p not in sys.path:
        sys.path.append(_p)

print(f"[INFO] BACKEND_DIR:    {BACKEND_DIR}")
print(f"[INFO] NLP_UTILS_DIR:  {NLP_UTILS_DIR}")
print(f"[INFO] complete_pipeline.py exists: {os.path.exists(os.path.join(NLP_UTILS_DIR, 'complete_pipeline.py'))}")

try:
    from complete_pipeline import ThaiTextSegmenter
    HAS_PIPELINE = True
    print("[OK] complete_pipeline imported successfully")
except Exception as e:
    print(f"[WARN] Could not import complete_pipeline: {e}")
    HAS_PIPELINE = False

router = APIRouter()

RESULTS_DIR = os.path.join(BACKEND_DIR, "results")

# Singleton segmenter
_segmenter = None

def get_segmenter():
    """Get or initialize the Thai text segmenter"""
    global _segmenter
    
    if _segmenter is not None:
        return _segmenter

    if not HAS_PIPELINE:
        raise HTTPException(
            status_code=500,
            detail=f"Thai NLP pipeline not available. complete_pipeline.py not found in: {NLP_UTILS_DIR}"
        )
    
    try:
        BASE_PATH = os.path.join(BACKEND_DIR, "models")

        MTU_MODEL      = os.path.join(BASE_PATH, "mtu_crf_model.pkl")
        SYLLABLE_MODEL = os.path.join(BASE_PATH, "syllable_crf_model.pkl")
        DICT_MODEL     = os.path.join(BASE_PATH, "lst20_dictionary.pkl")
        POS_MODEL      = os.path.join(BASE_PATH, "pos_crf_model_modified.pkl")

        print(f"[INFO] Looking for models in: {BASE_PATH}")
        print(f"   mtu_crf_model.pkl          exists: {os.path.exists(MTU_MODEL)}")
        print(f"   syllable_crf_model.pkl     exists: {os.path.exists(SYLLABLE_MODEL)}")
        print(f"   lst20_dictionary.pkl       exists: {os.path.exists(DICT_MODEL)}")
        print(f"   pos_crf_model_modified.pkl exists: {os.path.exists(POS_MODEL)}")

        # Check missing models
        missing = []
        if not os.path.exists(MTU_MODEL):      missing.append("mtu_crf_model.pkl")
        if not os.path.exists(SYLLABLE_MODEL): missing.append("syllable_crf_model.pkl")
        if not os.path.exists(DICT_MODEL):     missing.append("lst20_dictionary.pkl")
        if not os.path.exists(POS_MODEL):      missing.append("pos_crf_model_modified.pkl")

        if missing:
            raise HTTPException(
                status_code=500,
                detail=f"Missing model files: {', '.join(missing)}. Please train models first."
            )

        print("[INFO] Initializing Thai NLP Pipeline...")
        _segmenter = ThaiTextSegmenter(
            MTU_MODEL,
            SYLLABLE_MODEL,
            DICT_MODEL,
            POS_MODEL
        )
        print("[OK] Pipeline initialized successfully")
        return _segmenter
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to initialize pipeline: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize NLP pipeline: {str(e)}"
        )


# =====================================================
# Request Models
# =====================================================
MAX_TEXT_CHARS = 10_000
MAX_HTML_CHARS = 200_000


class ProcessHtmlRequest(BaseModel):
    html: str
    tag: Optional[str] = None
    cssClass: Optional[str] = None
    css_class: Optional[str] = None

class SegmentTextRequest(BaseModel):
    text: str

class ExportTrainingRequest(BaseModel):
    original_text: str
    segmented_words: List[str]
    confidence: float
    metadata: Optional[dict] = None


def _read_json_if_exists(path: str):
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _segment_text_unified(segmenter, text: str):
    """Unified segmentation output for both HTML and Text endpoints."""
    from features.pos_features import extract_features as extract_pos_features

    words: List[str] = []
    detailed_results = []
    confidence_scores: List[float] = []

    for chunk in re.split(r'(\s+)', text):
        if chunk == "":
            continue

        if re.match(r'^\s+$', chunk):
            words.append(' ')
            detailed_results.append(
                {
                    "word": ' ',
                    "pos": "PU",
                    "syllables": [' '],
                    "confidence": None,
                }
            )
            continue

        results = segmenter.segment_with_pos_and_syllables(chunk, show_debug=False)
        chunk_words = [word for word, _, _ in results]
        chunk_confidences: List[float] = []

        if chunk_words:
            pos_features = extract_pos_features(chunk_words)
            pos_marginals = segmenter.pos_crf.predict_marginals([pos_features])[0]
            chunk_confidences = [max(m.values(), default=0.0) for m in pos_marginals]

        for i, (word, pos, syllables) in enumerate(results):
            token_conf = chunk_confidences[i] if i < len(chunk_confidences) else 0.0
            words.append(word)
            confidence_scores.append(token_conf)
            detailed_results.append(
                {
                    "word": word,
                    "pos": pos,
                    "syllables": syllables,
                    "confidence": round(token_conf, 4),
                }
            )

    overall_confidence = (
        sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
    )

    return {
        "words": words,
        "detailed": detailed_results,
        "confidence": round(overall_confidence, 4),
    }


# =====================================================
# Routes
# =====================================================
@router.post("/process-html")
async def process_html(request: ProcessHtmlRequest):
    """Process HTML by segmenting Thai text and wrapping words with <wbr> tags"""
    try:
        if not request.html or not request.html.strip():
            raise HTTPException(status_code=400, detail="HTML content is required")
        if len(request.html) > MAX_HTML_CHARS:
            raise HTTPException(status_code=413, detail=f"HTML content exceeds maximum size of {MAX_HTML_CHARS} characters")
        
        segmenter = get_segmenter()

        wrap_tag = (request.tag or "span").lower()
        if wrap_tag not in {"span", "div"}:
            wrap_tag = "span"

        css_class = (request.cssClass if request.cssClass is not None else request.css_class) or ""
        css_class = css_class.strip()

        thai_word_pattern = re.compile(r'[\u0E00-\u0E7F]')

        def wrap_words(words: List[str]) -> str:
            wrapped_parts: List[str] = []
            for word in words:
                if thai_word_pattern.search(word):
                    if css_class:
                        wrapped_parts.append(f'<wbr><{wrap_tag} class="{css_class}">{word}</{wrap_tag}>')
                    else:
                        wrapped_parts.append(f'<wbr><{wrap_tag}>{word}</{wrap_tag}>')
                else:
                    wrapped_parts.append(word)
            return ''.join(wrapped_parts)

        thai_pattern = re.compile(r'[\u0E00-\u0E7F]+(?:\s+[\u0E00-\u0E7F]+)*')
        wrapped_html = request.html
        matches = list(thai_pattern.finditer(request.html))
        confidence_scores: List[float] = []
        segmented_chunks: List[tuple] = []
        
        for match in reversed(matches):
            thai_text = match.group()
            segmented = _segment_text_unified(segmenter, thai_text)
            segmented_chunks.append((match.start(), segmented["words"]))
            confidence_scores.extend(
                d["confidence"]
                for d in segmented["detailed"]
                if d.get("confidence") is not None
            )
            wrapped_text = wrap_words(segmented["words"])
            wrapped_html = (
                wrapped_html[:match.start()] + 
                wrapped_text + 
                wrapped_html[match.end():]
            )
        
        segment_count = wrapped_html.count('<wbr>')
        segmented_words: List[str] = []
        for _, words in sorted(segmented_chunks, key=lambda x: x[0]):
            segmented_words.extend(words)
        overall_confidence = (
            sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        )
        
        return {
            "success": True,
            "data": {
                "wrapped_html": wrapped_html,
                "processed_html": wrapped_html,
                "segment_count": segment_count,
                "segmented_words": segmented_words,
                "confidence": round(overall_confidence, 4),
                "original_length": len(request.html),
                "processed_length": len(wrapped_html)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing HTML: {str(e)}")
        return {"success": False, "error": "Processing failed"}


@router.post("/text-process")
async def segment_text(request: SegmentTextRequest):
    """Segment plain Thai text into words using full NLP pipeline"""
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text is required")
        if len(request.text) > MAX_TEXT_CHARS:
            raise HTTPException(status_code=413, detail=f"Text exceeds maximum size of {MAX_TEXT_CHARS} characters")
        
        segmenter = get_segmenter()
        segmented = _segment_text_unified(segmenter, request.text.strip())
        
        return {
            "success": True,
            "data": {
                "words": segmented["words"],
                "word_count": len(segmented["words"]),
                "confidence": segmented["confidence"],
                "detailed": segmented["detailed"],
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error segmenting text: {str(e)}")
        return {"success": False, "error": "Segmentation failed"}


@router.post("/export-training")
async def export_training_data(request: ExportTrainingRequest, _user: dict = Depends(require_auth)):
    """Save training data for model retraining"""
    try:
        import json
        from datetime import datetime

        training_dir = os.path.join(BACKEND_DIR, "data", "training_exports")
        os.makedirs(training_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(training_dir, f"training_{timestamp}.json")

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "original_text": request.original_text,
                "segmented_words": request.segmented_words,
                "confidence": request.confidence,
                "metadata": request.metadata or {},
                "timestamp": timestamp
            }, f, ensure_ascii=False, indent=2)

        print(f"[OK] Training data saved: {filepath}")
        return {"success": True, "message": "Training data saved"}

    except Exception as e:
        print(f"Error exporting training data: {str(e)}")
        return {"success": False, "error": "Export failed"}


@router.get("/metrics")
async def get_metrics(_user: dict = Depends(require_auth)):
    """Return latest offline evaluation metrics from backend/results/*.json"""
    try:
        files = {
            "evaluation": os.path.join(RESULTS_DIR, "evaluation_results.json"),
            "mtu": os.path.join(RESULTS_DIR, "mtu_results.json"),
            "syllable": os.path.join(RESULTS_DIR, "syllable_results.json"),
            "word_seg": os.path.join(RESULTS_DIR, "word_seg_results.json"),
            "pos": os.path.join(RESULTS_DIR, "pos_results.json"),
        }

        data = {name: _read_json_if_exists(path) for name, path in files.items()}
        available = [name for name, payload in data.items() if payload is not None]

        if not available:
            raise HTTPException(
                status_code=404,
                detail=f"No evaluation files found in: {RESULTS_DIR}"
            )

        return {
            "success": True,
            "data": {
                "available": available,
                "results": data,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error loading metrics: {str(e)}")
        return {"success": False, "error": "Failed to load metrics"}


# @router.get("/health")
# async def health_check():
#     """Check if the NLP pipeline is ready"""
#     try:
#         segmenter = get_segmenter()
#         return {
#             "status": "healthy",
#             "pipeline_loaded": segmenter is not None,
#             "service": "thai-nlp"
#         }
#     except Exception as e:
#         return {
#             "status": "unhealthy",
#             "pipeline_loaded": False,
#             "error": str(e)
#         }
