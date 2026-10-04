from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.auth import router as auth_router
from app.routes.donations import router as donations_router
from app.routes.requests import router as requests_router
from app.routes.organizations import router as organizations_router
from app.routes.admin import router as admin_router
from app.routes.ai import router as ai_router

from app.seed.demo_data import seed_demo_data


app = FastAPI(
    title="Smart Food Waste Management API",
    description="AI-powered food donation platform",
    version="1.0.0",
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# API ROUTES
# ============================================================

app.include_router(auth_router)
app.include_router(donations_router)
app.include_router(requests_router)
app.include_router(organizations_router)
app.include_router(admin_router)
app.include_router(ai_router)


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup_event():
    seed_demo_data()


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "success": True,
        "message": "Smart Food Waste Management API is running!",
    }