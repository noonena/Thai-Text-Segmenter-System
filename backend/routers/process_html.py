"""
API Router for Thai Text Processing
Uses complete_pipeline.py from backend/scripts/nlp_utils/
"""

import os
import sys

# =====================================================
# Setup paths FIRST
# =====================================================
# This file is at: backend/routers/process_html.py
# So BACKEND_DIR = backend/
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# complete_pipeline.py is at: backend/scripts/nlp_utils/
NLP_UTILS_DIR = os.path.join(BACKEND_DIR, "scripts", "nlp_utils")

# Add ALL needed directories to path
MODELS_DIR = os.path.join(NLP_UTILS_DIR, "models")
SCRIPTS_MODELS_DIR = os.path.join(BACKEND_DIR, "scripts", "models")

sys.path.insert(0, BACKEND_DIR)
# sys.path.insert(0, SCRIPTS_DIR)
sys.path.insert(0, NLP_UTILS_DIR)
sys.path.insert(0, MODELS_DIR)
sys.path.insert(0, SCRIPTS_MODELS_DIR)

print(f"🔍 BACKEND_DIR:    {BACKEND_DIR}")
print(f"🔍 NLP_UTILS_DIR:  {NLP_UTILS_DIR}")
print(f"🔍 complete_pipeline.py exists: {os.path.exists(os.path.join(NLP_UTILS_DIR, 'complete_pipeline.py'))}")

# =====================================================
# Import pipeline AFTER path setup
# =====================================================
try:
    from complete_pipeline import ThaiTextSegmenter
    HAS_PIPELINE = True
    print("✅ complete_pipeline imported successfully")
except ImportError as e:
    print(f"⚠️  Could not import complete_pipeline: {e}")
    HAS_PIPELINE = False

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import re

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
        
        SYLLABLE_MODEL = os.path.join(BASE_PATH, "syllable_crf_model.pkl")
        DICT_MODEL     = os.path.join(BASE_PATH, "lst20_dictionary.pkl")
        POS_MODEL      = os.path.join(BASE_PATH, "pos_crf_model.pkl")

        print(f"🔍 Looking for models in: {BASE_PATH}")
        print(f"   syllable_crf_model.pkl exists: {os.path.exists(SYLLABLE_MODEL)}")
        print(f"   lst20_dictionary.pkl   exists: {os.path.exists(DICT_MODEL)}")
        print(f"   pos_crf_model.pkl      exists: {os.path.exists(POS_MODEL)}")
        print(f"   MTU stage: TCC rules (no model file needed)")

        # Check missing models
        missing = []
        if not os.path.exists(SYLLABLE_MODEL): missing.append("syllable_crf_model.pkl")
        if not os.path.exists(DICT_MODEL):     missing.append("lst20_dictionary.pkl")
        if not os.path.exists(POS_MODEL):      missing.append("pos_crf_model.pkl")
        
        if missing:
            raise HTTPException(
                status_code=500,
                detail=f"Missing model files: {', '.join(missing)}. Please train models first."
            )
        
        print("🚀 Initializing Thai NLP Pipeline...")
        _segmenter = ThaiTextSegmenter(
            None,           # MTU model path — unused, TCC rules handle this stage
            SYLLABLE_MODEL,
            DICT_MODEL,
            POS_MODEL
        )
        print("✅ Pipeline initialized successfully")
        return _segmenter
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Failed to initialize pipeline: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize NLP pipeline: {str(e)}"
        )


# =====================================================
# Request Models
# =====================================================
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
        
        segmenter = get_segmenter()
        
        thai_pattern = re.compile(r'[\u0E00-\u0E7F]+(?:\s+[\u0E00-\u0E7F]+)*')
        wrapped_html = request.html
        matches = list(thai_pattern.finditer(request.html))
        
        for match in reversed(matches):
            thai_text = match.group()
            words = segmenter.segment_words(thai_text)
            wrapped_text = '<wbr>'.join(words)
            wrapped_html = (
                wrapped_html[:match.start()] + 
                wrapped_text + 
                wrapped_html[match.end():]
            )
        
        segment_count = wrapped_html.count('<wbr>')
        
        return {
            "success": True,
            "data": {
                "wrapped_html": wrapped_html,
                "processed_html": wrapped_html,
                "segment_count": segment_count,
                "original_length": len(request.html),
                "processed_length": len(wrapped_html)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing HTML: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post("/segment")
async def segment_text(request: SegmentTextRequest):
    """Segment plain Thai text into words using full NLP pipeline"""
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text is required")
        
        segmenter = get_segmenter()
        
        results = segmenter.segment_with_pos_and_syllables(
            request.text,
            show_debug=False
        )
        
        words = [word for word, pos, syllables in results]
        detailed_results = [
            {"word": word, "pos": pos, "syllables": syllables}
            for word, pos, syllables in results
        ]
        
        return {
            "success": True,
            "data": {
                "words": words,
                "word_count": len(words),
                "confidence": 0.95,
                "detailed": detailed_results
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error segmenting text: {str(e)}")
        return {"success": False, "error": str(e)}


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
        
        print(f"✅ Training data saved: {filepath}")
        return {"success": True, "message": "Training data saved", "filepath": filepath}
        
    except Exception as e:
        print(f"Error exporting training data: {str(e)}")
        return {"success": False, "error": str(e)}


@router.get("/health")
async def health_check():
    """Check if the NLP pipeline is ready"""
    try:
        segmenter = get_segmenter()
        return {
            "status": "healthy",
            "pipeline_loaded": segmenter is not None,
            "service": "thai-nlp"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "pipeline_loaded": False,
            "error": str(e)
        }