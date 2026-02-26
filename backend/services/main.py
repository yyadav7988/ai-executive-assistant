from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base

# Import API routers (will create these next)
# from app.api import auth, emails, calendar, brief, activity, preferences

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="AI Executive Assistant API",
    description="Production-grade AI-powered executive assistant for Gmail and Calendar management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-executive-assistant"}

# Include routers (will uncomment after creating them)
# app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
# app.include_router(emails.router, prefix="/api/emails", tags=["Emails"])
# app.include_router(calendar.router, prefix="/api/calendar", tags=["Calendar"])
# app.include_router(brief.router, prefix="/api/brief", tags=["Today's Brief"])
# app.include_router(activity.router, prefix="/api/activity", tags=["Activity"])
# app.include_router(preferences.router, prefix="/api/preferences", tags=["Preferences"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
