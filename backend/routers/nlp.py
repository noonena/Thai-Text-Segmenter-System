"""
API Router for Thai Text Processing
Uses complete_pipeline.py from backend/scripts/nlp_utils/
"""

import os
import sys
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import re
from scripts.nlp_utils.complete_pipeline import SegmentStats

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

class SegmentTextRequest(BaseModel):
    text: str

class ExportTrainingRequest(BaseModel):
    original_text: str
    segmented_words: List[str]
    confidence: float
    metadata: Optional[dict] = None


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
        stats: SegmentStats = SegmentStats()
        thai_pattern = re.compile(r'[\u0E00-\u0E7F]+(?:\s+[\u0E00-\u0E7F]+)*')
        wrapped_html = request.html
        matches = list(thai_pattern.finditer(request.html))

        for match in reversed(matches):
            thai_text = match.group()
            words, _stats = segmenter.segment_words(thai_text)
            stats.append(_stats)
            wrapped_text = '<wbr>'.join(words)
            wrapped_html = (
                wrapped_html[:match.start()] +
                wrapped_text +
                wrapped_html[match.end():]
            )

        segment_count = wrapped_html.count('<wbr>')
        stats.compile()

        return {
            "success": True,
            "data": {
                "wrapped_html": wrapped_html,
                "processed_html": wrapped_html,
                "segment_count": segment_count,
                "original_length": len(request.html),
                "processed_length": len(wrapped_html),
                "token_count": stats.tok_count if stats else None,
                "tokenize_tps": stats.tokenize_spd if stats else None,
                "segment_tps": stats.segment_spd if stats else None,
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

        # Split on whitespace, process each chunk separately, preserve spaces as separators
        words = []
        stats: SegmentStats = SegmentStats()
        detailed_results = []
        start_epoch = time.time()
        chunk_count = 0
        for chunk in re.split(r'(\s+)', request.text.strip()):
            if not chunk:
                continue

            chunk_count += 1
            if re.match(r'^\s+$', chunk):
                # Keep space as a separator token
                words.append(' ')
                detailed_results.append({"word": ' ', "pos": "PU", "syllables": [' ']})
            else:
                results, _stats = segmenter.segment_with_pos_and_syllables(chunk, show_debug=False)
                stats.append(_stats)
                for word, pos, syllables in results:
                    words.append(word)
                    detailed_results.append({"word": word, "pos": pos, "syllables": syllables})
        end_epoch = time.time()
        processing_time = end_epoch - start_epoch
        stats.compile()

        return {
            "success": True,
            "data": {
                "chunks": chunk_count,
                "word_count": len(words),
                "chunks_cps": chunk_count / processing_time if processing_time > 0 else None,
                "token_count": stats.tok_count if stats else None,
                "tokenize_tps": stats.tokenize_spd if stats else None,
                "segment_tps": stats.segment_spd if stats else None,
                "postprocess_tps": stats.postprocess_spd if stats else None,
                "words": words,
                "detailed": detailed_results
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error segmenting text: {str(e)}")
        return {"success": False, "error": "Segmentation failed"}


@router.post("/export-training")
async def export_training_data(request: ExportTrainingRequest):
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
