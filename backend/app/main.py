import os
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env BEFORE importing modules that read them
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import auth, parser, generator

# ---------------------------------------------------------------------------
# App & CORS
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI-Based Automatic Verilog Testbench Generator",
    description="Backend API for parsing Verilog and generating testbenches via AI.",
    version="1.0.0",
)

# Allow all origins for local dev; tighten in production with VITE_API_URL origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# In-memory user store (for demo). Replace with a real DB in production.
# ---------------------------------------------------------------------------

USERS = {}  # username -> hashed password


def _ensure_demo_user():
    username = os.getenv("DEMO_USERNAME", "demo")
    password = os.getenv("DEMO_PASSWORD", "demo123")
    if username not in USERS:
        USERS[username] = auth.hash_password(password)


_ensure_demo_user()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class GenerateRequest(BaseModel):
    code: str


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ", 1)[1]
    payload = auth.decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload["sub"]


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {"message": "Verilog Testbench Generator API", "status": "ok"}


@app.post("/api/register")
def register(req: RegisterRequest):
    username = req.username.strip()
    password = req.password
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    if username in USERS:
        raise HTTPException(status_code=400, detail="Username already exists")
    USERS[username] = auth.hash_password(password)
    token = auth.create_access_token({"sub": username})
    return {"token": token, "username": username}


@app.post("/api/login")
def login(req: LoginRequest):
    username = req.username.strip()
    password = req.password
    hashed = USERS.get(username)
    if not hashed or not auth.verify_password(password, hashed):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = auth.create_access_token({"sub": username})
    return {"token": token, "username": username}


@app.get("/api/me")
def me(current_user: str = Depends(get_current_user)):
    return {"username": current_user}


# ---------------------------------------------------------------------------
# Verilog endpoints
# ---------------------------------------------------------------------------

@app.post("/api/parse")
def parse_code(req: GenerateRequest, current_user: str = Depends(get_current_user)):
    """Parse Verilog source and return extracted metadata."""
    try:
        metadata = parser.parse_verilog(req.code)
        return metadata
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Parsing failed: {exc}")


@app.post("/api/generate")
def generate_code(req: GenerateRequest, current_user: str = Depends(get_current_user)):
    """Render a testbench for the given Verilog module."""
    try:
        metadata = parser.parse_verilog(req.code)
        result = generator.generate_testbench(metadata)
        return {
            "testbench": result["testbench"],
            "metadata": metadata,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {exc}",
        )
