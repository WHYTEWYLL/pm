"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from . import oauth, tenant, workflows, stripe, local_dev, auth

app = FastAPI(
    title="PM Assistant API",
    description="AI-powered PM Assistant SaaS Platform",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(oauth.router)
app.include_router(workflows.router)

# Stripe router (optional)
try:
    app.include_router(stripe.router)
except Exception:
    pass  # Stripe not available

# Local dev router (only in development)
if os.getenv("ENV") != "production":
    app.include_router(local_dev.router)


@app.get("/")
async def root():
    return {"message": "PM Assistant API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

