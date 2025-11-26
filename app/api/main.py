"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from . import oauth, tenant, workflows, stripe, auth

app = FastAPI(
    title="PM Assistant API",
    description="AI-powered PM Assistant SaaS Platform",
    version="1.0.0",
)

# Determine allowed origins for CORS
frontend_origin = os.getenv("FRONTEND_ORIGIN")
default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Add production domain (corta.ai) - always included
production_origins = [
    "https://www.corta.ai",
    "https://corta.ai",
]
default_origins.extend(production_origins)

# Add Railway frontend domain if specified
railway_static_url = os.getenv("RAILWAY_STATIC_URL")
if railway_static_url:
    # Handle both http and https
    if railway_static_url.startswith("http"):
        default_origins.append(railway_static_url)
    else:
        default_origins.append(f"https://{railway_static_url}")
        default_origins.append(f"http://{railway_static_url}")

# Add Railway public domain (for frontend services)
# Set RAILWAY_PUBLIC_DOMAIN=loving-strength-production.up.railway.app in Railway
railway_public_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
if railway_public_domain:
    if railway_public_domain.startswith("http"):
        default_origins.append(railway_public_domain)
    else:
        default_origins.append(f"https://{railway_public_domain}")
        default_origins.append(f"http://{railway_public_domain}")

# Add custom frontend origin if specified
if frontend_origin:
    if isinstance(frontend_origin, str):
        # Handle comma-separated list of origins
        for origin in frontend_origin.split(","):
            origin = origin.strip()
            if origin and origin not in default_origins:
                default_origins.append(origin)
    else:
    default_origins.append(frontend_origin)

# Always use regex pattern to allow Railway domains
# This allows both corta.ai and any Railway *.up.railway.app domain
railway_pattern = r"^https?://.*\.up\.railway\.app$"
app.add_middleware(
    CORSMiddleware,
    allow_origins=default_origins,
    allow_origin_regex=railway_pattern,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
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


@app.get("/")
async def root():
    return {"message": "PM Assistant API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/debug/cors")
async def debug_cors():
    """Debug endpoint to check CORS configuration."""
    return {
        "allowed_origins": default_origins,
        "env": os.getenv("ENV", "not_set"),
        "frontend_origin": os.getenv("FRONTEND_ORIGIN"),
        "railway_static_url": os.getenv("RAILWAY_STATIC_URL"),
        "railway_public_domain": os.getenv("RAILWAY_PUBLIC_DOMAIN"),
        "railway_regex_enabled": os.getenv("ENV") == "production",
        "railway_regex_pattern": (
            r"^https?://.*\.up\.railway\.app$"
            if os.getenv("ENV") == "production"
            else None
        ),
    }
