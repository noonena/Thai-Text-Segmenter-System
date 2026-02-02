# # backend/app.py
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import List, Optional
# import pickle
# import os
# from pathlib import Path
# import re
# from bs4 import BeautifulSoup

# # Import your MTU functions
# import sys
# sys.path.append(str(Path(__file__).parent / 'scripts'))
# from scripts.utils.features import (
#     load_model,
#     segment_text_to_mtus,
#     format_mtus,
# )

# # Import complete pipeline components
# from scripts.complete_pipeline import ThaiTextSegmenterWithPOS

# app = FastAPI(
#     title="MTU Segmentation API",
#     description="API for Thai Minimum Text Unit segmentation",
#     version="1.0.0",
#     default_response_encoding="utf-8"
# )

# # Enable CORS for React frontend
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Load models once when server starts
# MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'mtu_crf_model.pkl')
# DICT_PATH = os.path.join(os.path.dirname(__file__), 'models', 'lst20_dictionary.pkl')

# crf_model = None
# segmenter = None

# @app.on_event("startup")
# async def load_model_on_startup():
#     global crf_model, segmenter
#     try:
#         # Load simple CRF model
#         crf_model = load_model(MODEL_PATH)
#         print(f"MTU model loaded successfully from {MODEL_PATH}")
        
#         # Load complete pipeline segmenter
#         segmenter = ThaiTextSegmenterWithPOS(MODEL_PATH, DICT_PATH)
#         print(f"Complete pipeline loaded successfully")
#     except Exception as e:
#         print(f"Error loading models: {e}")


# # Request/Response models
# class SegmentRequest(BaseModel):
#     text: str

# class BatchSegmentRequest(BaseModel):
#     texts: List[str]

# class SegmentResponse(BaseModel):
#     success: bool
#     text: str
#     mtus: List[str]
#     formatted: str
#     labels: List[str]
#     count: int

# class HTMLProcessRequest(BaseModel):
#     html_content: str
#     filename: str
#     settings: dict  # {"tag": "span", "cssClass": "no-wrap"}

# class HTMLProcessResponse(BaseModel):
#     success: bool
#     wrapped_html: str
#     error: Optional[str] = None

# class ErrorResponse(BaseModel):
#     success: bool
#     error: str


# @app.get("/")
# async def home():
#     """Health check endpoint"""
#     return {
#         "status": "running",
#         "message": "MTU Segmentation API",
#         "model_loaded": crf_model is not None,
#         "segmenter_loaded": segmenter is not None,
#         "docs": "/docs"
#     }

# # Replace the /api/segment endpoint in your app.py with this:

# @app.post("/api/segment")
# async def segment(request: SegmentRequest):
#     """
#     Segment Thai text into words
    
#     Example:
#     ```
#     POST /api/segment
#     {
#         "text": "สวัสดีครับ"
#     }
#     ```
#     """
#     if segmenter is None:  # ← Changed from crf_model
#         raise HTTPException(status_code=500, detail="Segmenter not loaded")
    
#     if not request.text:
#         raise HTTPException(status_code=400, detail="No text provided")
    
#     try:
#         # Use complete pipeline (same as HTML endpoint!)
#         words = segmenter.segment(request.text.strip())
        
#         return {
#             "success": True,
#             "text": request.text,
#             "words": words,  # ← Changed from mtus to words
#             "count": len(words)
#         }
    
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=str(e))


# # Also update the response model:
# class SegmentResponseUpdated(BaseModel):
#     success: bool
#     text: str
#     words: List[str]  # ← Changed from mtus: List[str]
#     count: int

# @app.post("/api/batch-segment")
# async def batch_segment(request: BatchSegmentRequest):
#     """
#     Segment multiple texts
    
#     Example:
#     ```
#     POST /api/batch-segment
#     {
#         "texts": ["สวัสดี", "กาแฟ", "เชื่อ"]
#     }
#     ```
#     """
#     if crf_model is None:
#         raise HTTPException(status_code=500, detail="Model not loaded")
    
#     if not request.texts:
#         raise HTTPException(status_code=400, detail="No texts provided")
    
#     try:
#         results = []
#         for text in request.texts:
#             mtus, labels, _ = segment_text_to_mtus(text, crf_model)
#             mtu_list = [''.join(mtu) for mtu in mtus]
#             results.append({
#                 "text": text,
#                 "mtus": mtu_list,
#                 "formatted": format_mtus(mtus)
#             })
        
#         return {
#             "success": True,
#             "results": results,
#             "count": len(results)
#         }
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.post("/api/process-html", response_model=HTMLProcessResponse)
# async def process_html(request: HTMLProcessRequest):
#     """
#     Process HTML file - extract Thai text, segment into words, and wrap with specified tags
    
#     Example:
#     ```
#     POST /api/process-html
#     {
#         "html_content": "<html><body><p>สวัสดีครับ</p></body></html>",
#         "filename": "test.html",
#         "settings": {
#             "tag": "span",
#             "cssClass": "no-wrap"
#         }
#     }
#     ```
#     """
#     if segmenter is None:
#         raise HTTPException(status_code=500, detail="Segmenter not loaded")
    
#     try:
# # Parse HTML
#         soup = BeautifulSoup(request.html_content, 'html.parser')
        
#         # Get settings
#         tag = request.settings.get("tag", "span")
#         css_class = request.settings.get("cssClass", "")
        
#         # Only process body content, leave head untouched
#         body = soup.find('body')
#         if not body:
#             # If no body tag, process entire document
#             body = soup
#         def process_text_node(text):
#             """Process a single text node - segment and wrap Thai words"""
#             if not text or not text.strip():
#                 return text
            
#             # Check if text contains Thai characters
#             if not re.search(r'[\u0E00-\u0E7F]', text):
#                 return text
            
#             try:
#                 # Segment the text using complete pipeline
#                 words = segmenter.segment(text.strip())
                
#                 # Build wrapped HTML
#                 wrapped_parts = []
#                 for word in words:
#                     # Check if word is Thai
#                     if re.search(r'[\u0E00-\u0E7F]', word):
#                         # Wrap Thai words
#                         if css_class:
#                             wrapped_parts.append(f'<wbr><{tag} class="{css_class}">{word}</{tag}>')
#                         else:
#                             wrapped_parts.append(f'<wbr><{tag}>{word}</{tag}>')
#                     else:
#                         # Keep non-Thai text as is
#                         wrapped_parts.append(word)
                
#                 return ''.join(wrapped_parts)
#             except Exception as e:
#                 print(f"Error processing text: {text[:50]}... Error: {e}")
#                 return text
        
#         # Find all text nodes and process them
#         for element in soup.find_all(text=True):
#             # Skip script and style tags
#             if element.parent.name in ['script', 'style']:
#                 continue
            
#             # Process the text
#             new_text = process_text_node(str(element))
            
#             # Replace with new wrapped version
#             if new_text != str(element):
#                 # Create new soup from wrapped text
#                 new_soup = BeautifulSoup(new_text, 'html.parser')
#                 element.replace_with(new_soup)
        
#         # Return processed HTML
#         wrapped_html = str(soup)
        
#         return {
#             "success": True,
#             "wrapped_html": wrapped_html,
#             "error": None
#         }
    
#     except Exception as e:
#         import traceback
#         error_detail = f"{str(e)}\n{traceback.format_exc()}"
#         print(f"Error processing HTML: {error_detail}")
#         raise HTTPException(status_code=500, detail=str(e))


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

# backend/app.py
# FIXED VERSION WITH WINDOWS ENCODING SUPPORT

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pickle
import os
from pathlib import Path
import re
from bs4 import BeautifulSoup
import sys

# ✅ FIX 1: Set default encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors='replace')

# Import your MTU functions
# from backend.scripts.utils.features import (
#     load_model,
#     segment_text_to_mtus,
#     format_mtus,
# )

# # Import complete pipeline components
# sys.path.append(str(Path(__file__).parent / 'scripts'))
# from backend.scripts.complete_pipeline import ThaiTextSegmenterWithPOS

# Import your MTU functions
import sys
sys.path.append(str(Path(__file__).parent / 'scripts'))
from scripts.utils.features import (
    load_model,
    segment_text_to_mtus,
    format_mtus,
)

# Import complete pipeline components
from scripts.complete_pipeline import ThaiTextSegmenterWithPOS

app = FastAPI(
    title="MTU Segmentation API",
    description="API for Thai Minimum Text Unit segmentation",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load models once when server starts
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'mtu_crf_model.pkl')
DICT_PATH = os.path.join(os.path.dirname(__file__), 'models', 'lst20_dictionary.pkl')

crf_model = None
segmenter = None

@app.on_event("startup")
async def load_model_on_startup():
    global crf_model, segmenter
    try:
        # ✅ FIX 2: Load models with explicit encoding
        with open(MODEL_PATH, 'rb') as f:
            crf_model = pickle.load(f)
        print(f"✅ MTU model loaded successfully from {MODEL_PATH}")
        
        # Load complete pipeline segmenter
        segmenter = ThaiTextSegmenterWithPOS(MODEL_PATH, DICT_PATH)
        print(f"✅ Complete pipeline loaded successfully")
    except Exception as e:
        print(f"❌ Error loading models: {e}")
        import traceback
        traceback.print_exc()


# Request/Response models
class SegmentRequest(BaseModel):
    text: str
    
    class Config:
        # ✅ FIX 3: Ensure Pydantic handles UTF-8 correctly
        json_encoders = {
            str: lambda v: v.encode('utf-8').decode('utf-8')
        }

class BatchSegmentRequest(BaseModel):
    texts: List[str]

class SegmentResponse(BaseModel):
    success: bool
    text: str
    words: List[str]  # ✅ CHANGED: Return words instead of MTUs
    count: int

class HTMLProcessRequest(BaseModel):
    html_content: str
    filename: str
    settings: dict

class HTMLProcessResponse(BaseModel):
    success: bool
    wrapped_html: str
    segment_count: int = 0  # Add this line
    error: Optional[str] = None

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
        "segmenter_loaded": segmenter is not None,
        "docs": "/docs",
        "encoding": sys.getdefaultencoding()  # ✅ Show current encoding
    }


@app.post("/api/segment", response_model=SegmentResponse)
async def segment(request: SegmentRequest):
    """
    Segment Thai text into words using complete 3-layer pipeline
    
    Example:
    ```
    POST /api/segment
    {
        "text": "สวัสดีครับผมชื่อวิน"
    }
    
    Response:
    {
        "success": true,
        "text": "สวัสดีครับผมชื่อวิน",
        "words": ["สวัสดี", "ครับ", "ผม", "ชื่อ", "วิน"],
        "count": 5
    }
    ```
    """
    if segmenter is None:
        raise HTTPException(status_code=500, detail="Segmenter not loaded")
    
    if not request.text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    try:
        # ✅ FIX 4: Ensure text is properly encoded
        text = request.text.strip()
        
        # Verify it's UTF-8
        try:
            text.encode('utf-8')
        except UnicodeEncodeError as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Text encoding error: {str(e)}. Please ensure text is UTF-8 encoded."
            )
        
        # Segment using complete pipeline (3 layers)
        words = segmenter.segment(text)
        
        # ✅ FIX 5: Ensure all words are valid UTF-8 strings
        words = [str(word) for word in words if word]
        
        return {
            "success": True,
            "text": text,
            "words": words,  # Return segmented words
            "count": len(words)
        }
    
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"❌ Error in segment endpoint: {error_detail}")
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
    if segmenter is None:
        raise HTTPException(status_code=500, detail="Segmenter not loaded")
    
    if not request.texts:
        raise HTTPException(status_code=400, detail="No texts provided")
    
    try:
        results = []
        for text in request.texts:
            # Segment using complete pipeline
            words = segmenter.segment(text.strip())
            results.append({
                "text": text,
                "words": words,
                "count": len(words)
            })
        
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process-html", response_model=HTMLProcessResponse)
async def process_html(request: HTMLProcessRequest):
    """Process HTML file and return segment count"""
    if segmenter is None:
        raise HTTPException(status_code=500, detail="Segmenter not loaded")
    
    try:
        soup = BeautifulSoup(request.html_content, 'html.parser', from_encoding='utf-8')
        
        tag = request.settings.get("tag", "span")
        css_class = request.settings.get("cssClass", "")
        
        thai_pattern = re.compile(r'[\u0E00-\u0E7F]')
        segment_count = 0  # ✅ ADD THIS
        
        def process_text_node(text):
            nonlocal segment_count  # ✅ ADD THIS
            
            if not text or not text.strip():
                return text
            
            if not thai_pattern.search(text):
                return text
            
            try:
                text_clean = text.strip()
                words = segmenter.segment(text_clean)
                
                # ✅ ADD THIS: Count Thai words
                thai_word_count = sum(1 for word in words if thai_pattern.search(word))
                segment_count += thai_word_count
                
                wrapped_parts = []
                for word in words:
                    if thai_pattern.search(word):
                        if css_class:
                            wrapped_parts.append(f'<wbr><{tag} class="{css_class}">{word}</{tag}>')
                        else:
                            wrapped_parts.append(f'<wbr><{tag}>{word}</{tag}>')
                    else:
                        wrapped_parts.append(word)
                
                return ''.join(wrapped_parts)
                
            except Exception as e:
                print(f"❌ Error processing text node: {e}")
                return text
        
        # Process all text nodes
        for element in soup.find_all(text=True):
            if element.parent.name in ['script', 'style', 'meta', 'link']:
                continue
            
            original_text = str(element)
            new_text = process_text_node(original_text)
            
            if new_text != original_text:
                new_soup = BeautifulSoup(new_text, 'html.parser', from_encoding='utf-8')
                element.replace_with(new_soup)
        
        wrapped_html = str(soup)
        
        # ✅ IMPORTANT: Log the count
        print(f"✅ Successfully processed {segment_count} Thai word segments")
        
        return {
            "success": True,
            "wrapped_html": wrapped_html,
            "segment_count": segment_count,  # ✅ ADD THIS
            "error": None
        }
    
    except Exception as e:
        import traceback
        print(f"❌ Error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    # ✅ FIX 12: Run with explicit encoding for Windows
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        # Ensure UTF-8 encoding in logs
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        }
    )