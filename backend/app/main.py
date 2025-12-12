from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, user, admin
from app.routers import risk  # new ML / risk API
from app.routers.auth_whatsapp import router as whatsapp_auth_router


app = FastAPI(title="Early Risk Signals - Credit Card Delinquency")

# CORS origins: from env if set, else default to local dev URLs
if settings.CORS_ORIGINS:
    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
else:
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(admin.router)
app.include_router(risk.router)
app.include_router(whatsapp_auth_router)


@app.get("/")
def root():
    return {"message": "Credit Risk API running"}
