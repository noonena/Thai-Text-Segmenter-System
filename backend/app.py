from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, users, roles, process_html, stats

# Add this line:
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api")
async def api_info():
    return {"status": "running", "message": "Thai Text Segmenter API"}

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(roles.router, prefix="/api/roles", tags=["roles"])
app.include_router(process_html.router, prefix="/api", tags=["nlp"])
app.include_router(stats.router, prefix="/api", tags=["stats"])
