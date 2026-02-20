"""
Main entry point for Thai Text Segmenter Backend
"""
import sys
import os
from app import app

if __name__ == "__main__":
    import uvicorn
    
    print("Starting Thai Text Segmenter Backend...")
    print("API Documentation: http://localhost:8002/docs")
    print("Default login: admin / admin123")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )