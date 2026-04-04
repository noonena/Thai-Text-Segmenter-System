"""
Main entry point for Thai Text Segmenter Backend
"""
from app import app

def run():
    import uvicorn

    print("Starting Thai Text Segmenter Backend...")
    print("API Documentation: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

if __name__ == "__main__":
    run()
