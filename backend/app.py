# backend/app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import pickle
import os
from pathlib import Path

# Import your MTU functions
import sys
sys.path.append(str(Path(__file__).parent / 'src'))
from mtu.inference import load_model, segment_text_to_mtus, format_mtus

app = FastAPI(
    title="MTU Segmentation API",
    description="API for Thai Minimum Text Unit segmentation",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model once when server starts
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'mtu_crf_model.pkl')
crf_model = None

@app.on_event("startup")
async def load_model_on_startup():
    global crf_model
    try:
        crf_model = load_model(MODEL_PATH)
        print(f"✅ Model loaded successfully from {MODEL_PATH}")
    except Exception as e:
        print(f"❌ Error loading model: {e}")


# Request/Response models
class SegmentRequest(BaseModel):
    text: str

class BatchSegmentRequest(BaseModel):
    texts: List[str]

class SegmentResponse(BaseModel):
    success: bool
    text: str
    mtus: List[str]
    formatted: str
    labels: List[str]
    count: int

class ErrorResponse(BaseModel):
    success: bool
    error: str


@app.get("/")
async def home():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "MTU Segmentation API",
        "model_loaded": crf_model is not None,
        "docs": "/docs"
    }


@app.post("/api/segment", response_model=SegmentResponse)
async def segment(request: SegmentRequest):
    """
    Segment Thai text into MTUs
    
    Example:
    ```
    POST /api/segment
    {
        "text": "สวัสดีครับ"
    }
    ```
    """
    if crf_model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    if not request.text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    try:
        # Segment text
        mtus, labels, mtu_labels = segment_text_to_mtus(request.text, crf_model)
        formatted = format_mtus(mtus)
        
        # Convert to simple list of strings
        mtu_list = [''.join(mtu) for mtu in mtus]
        
        return {
            "success": True,
            "text": request.text,
            "mtus": mtu_list,
            "formatted": formatted,
            "labels": labels,
            "count": len(mtu_list)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/batch-segment")
async def batch_segment(request: BatchSegmentRequest):
    """
    Segment multiple texts
    
    Example:
    ```
    POST /api/batch-segment
    {
        "texts": ["สวัสดี", "กาแฟ", "เชื่อ"]
    }
    ```
    """
    if crf_model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    if not request.texts:
        raise HTTPException(status_code=400, detail="No texts provided")
    
    try:
        results = []
        for text in request.texts:
            mtus, labels, _ = segment_text_to_mtus(text, crf_model)
            mtu_list = [''.join(mtu) for mtu in mtus]
            results.append({
                "text": text,
                "mtus": mtu_list,
                "formatted": format_mtus(mtus)
            })
        
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)