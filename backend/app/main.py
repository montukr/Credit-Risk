from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, user, admin
from app.routers import risk  # new ML / risk API

app = FastAPI(title="Early Risk Signals - Credit Card Delinquency")

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

@app.get("/")
def root():
    return {"message": "Credit Risk API running"}
