# Deployment Guide

This document explains how to deploy the frontend to Vercel and the backend to Render.

## Prerequisites
- GitHub repo connected to both Vercel and Render (or you'll import manually)
- Do NOT commit secrets. Use Render/Vercel environment variable UI or GitHub Secrets.

---

## Backend (Render)

1. In Render, choose **New** → **Web Service** and connect your GitHub repository.
2. If asked, select the `backend` directory as the root (or let Render use `render.yaml`).
3. Build Command: `pip install -r requirements.txt` *(render.yaml already updated to install Rust for maturin builds)*
4. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variables in Render dashboard (Environment):
   - `SECRET_KEY` — generate a long random secret
   - `AI_PROVIDER` — `openrouter` or `openai`
   - `OPENROUTER_API_KEY` or `OPENAI_API_KEY` — your API key (secret)
   - `USE_AI` — `true` or `false`
   - `DEMO_USERNAME`, `DEMO_PASSWORD` — optional demo credentials
6. Deploy and note the backend URL (e.g. `https://your-backend.onrender.com`).

---

## Frontend (Vercel)

1. In Vercel, choose **New Project** → Import Git Repository.
2. Set Root Directory to `frontend`.
3. Build Command: `npm run build`.
4. Output Directory: `dist`.
5. Add Environment Variable in Vercel (Project Settings → Environment Variables):
   - `VITE_API_URL` = `https://your-backend.onrender.com` (set this BEFORE build)
6. Deploy. Note the frontend URL, then open it to verify requests hit the backend.

---

## Automating Vercel deploy (optional)

You can add a GitHub Action to call the Vercel CLI on push; this requires creating a `VERCEL_TOKEN` in GitHub Secrets. See `.github/workflows/deploy-vercel.yml` in this repo for an example.

## Local testing

Build frontend locally with the backend URL:

```bash
cd frontend
npm ci
VITE_API_URL="https://your-backend.onrender.com" npm run build
```

Run backend locally:

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

## Security

- Do not commit API keys or secrets. Use Render/Vercel/GitHub Secrets.
- If a secret was committed, rotate it immediately and remove it from history.

---

If you want, I can add the GitHub Action and push it, then help you set the required secrets in GitHub/Vercel/Render.
