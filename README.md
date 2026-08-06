# AI-Based Automatic Verilog Testbench Generator

Full-stack web application that uses AI (OpenAI / Gemini / OpenRouter) to automatically generate Verilog testbenches from a Verilog module design.

## ✨ Features

- **Dual-pane Monaco Editor** — write/edit Verilog on the left, view the generated testbench on the right.
- **File Upload** — upload `.v` / `.sv` files directly.
- **Verilog Parsing** — extracts module name, inputs/outputs, parameters, clock & reset signals using PyVerilog (with a regex fallback).
- **AI Generation** — synthesizes a structured prompt and generates a complete, syntactically correct testbench.
- **Offline Fallback** — if no AI key is configured, a template-based testbench generator is used automatically.
- **JWT Authentication** — login/register with bcrypt-hashed passwords and route protection.
- **Copy & Download** — one-click copy and download of the generated testbench as `.v`.

## 🏗️ Tech Stack

| Layer     | Technology                                      |
|-----------|-------------------------------------------------|
| Frontend  | React (Vite), Tailwind CSS, Monaco Editor, Lucide |
| Backend   | Python, FastAPI, PyVerilog, PyJWT, Passlib/Bcrypt |
| AI        | OpenAI API / Gemini API / OpenRouter API        |
| Deploy    | Vercel (frontend), Render (backend)             |

## 📁 Project Structure

```text
verilog-tb-generator/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI app, CORS, endpoints
│   │   ├── auth.py          # JWT auth & password hashing
│   │   ├── parser.py        # PyVerilog + regex parser
│   │   └── generator.py     # Prompt synthesis & AI integration
│   ├── requirements.txt
│   ├── .env.example
│   └── render.yaml          # Render deployment config
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Login.jsx
    │   │   ├── Header.jsx
    │   │   └── EditorView.jsx
    │   ├── App.jsx
    │   ├── main.jsx
    │   └── index.css
    ├── package.json
    ├── vite.config.js
    └── vercel.json
```

---

## 🚀 Local Development

### 1. Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

Configure environment variables:

```bash
# Copy and edit
copy .env.example .env
#    OR on macOS/Linux:
# cp .env.example .env
```

Set `AI_PROVIDER` and your API key in `.env` (OpenAI, Gemini, or OpenRouter). If you leave the key blank or set `USE_AI=false`, the app will use the built-in offline testbench generator.

Start the server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API is available at `http://localhost:8000`. Interactive docs at `/docs`.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # set VITE_API_URL if needed
npm run dev
```

Open `http://localhost:5173`.

### Demo Login

The backend auto-creates a demo user on startup:

- **Username:** `demo`
- **Password:** `demo123`

---

## 🔌 API Endpoints

| Method | Endpoint        | Auth | Description                          |
|--------|-----------------|------|--------------------------------------|
| POST   | `/api/register` | No   | Create an account (returns JWT)      |
| POST   | `/api/login`    | No   | Login (returns JWT)                  |
| GET    | `/api/me`       | Yes  | Get current user                     |
| POST   | `/api/parse`    | Yes  | Parse Verilog & return metadata      |
| POST   | `/api/generate` | Yes  | Generate a testbench for Verilog code|

---

## ☁️ Deployment

### Backend → Render

1. Push the `backend/` folder to a GitHub repo (or root of a repo).
2. In Render, create a **New Web Service**.
3. Connect the repo and set:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables from `.env` (especially `SECRET_KEY` and your AI API key).
5. Deploy.

Alternatively, a `backend/render.yaml` blueprint is included. You can use **Blueprint** → connect the repo and Render will pick it up.

### Frontend → Vercel

1. Push the `frontend/` folder to a GitHub repo (or root of a repo).
2. In Vercel, **Add New Project** and import the repo.
3. Set:
   - **Root Directory:** `frontend`
   - **Framework Preset:** `Vite`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. Add environment variable:
   - `VITE_API_URL` → your Render backend URL (e.g. `https://your-backend.onrender.com`)
5. Deploy.

The `vercel.json` rewrite rules handle SPA routing automatically.

---

## ⚙️ Environment Variables

### Backend (`backend/.env`)

| Variable             | Description                                        |
|----------------------|----------------------------------------------------|
| `SECRET_KEY`         | Secret for signing JWT tokens                     |
| `AI_PROVIDER`        | `openai`, `gemini`, or `openrouter`               |
| `USE_AI`             | `true` to use AI, `false` for offline generation  |
| `OPENAI_API_KEY`     | OpenAI key (provider = openai)                    |
| `GEMINI_API_KEY`     | Google Gemini key (provider = gemini)             |
| `OPENROUTER_API_KEY` | OpenRouter key (provider = openrouter)            |
| `OPENAI_MODEL`       | OpenAI model name (default `gpt-4o-mini`)         |
| `GEMINI_MODEL`       | Gemini model name (default `gemini-1.5-flash`)    |
| `OPENROUTER_MODEL`   | OpenRouter model slug                              |
| `DEMO_USERNAME`      | Demo account username (default `demo`)            |
| `DEMO_PASSWORD`      | Demo account password (default `demo123`)         |

### Frontend (`frontend/.env.local`)

| Variable       | Description                          |
|----------------|--------------------------------------|
| `VITE_API_URL` | Backend API base URL                 |

---

## 🧪 How It Works

1. **Parse** — `parser.py` uses PyVerilog to parse the Verilog module and extract ports, parameters, clocks, and resets. If PyVerilog fails on non-compliant syntax, a regex fallback parser kicks in.
2. **Prompt** — `generator.py` builds a detailed LLM prompt describing the module and the required testbench structure.
3. **Generate** — the AI provider returns a complete testbench with clock generation, reset sequence, stimulus vectors, and monitoring statements. If the AI call fails, a local template generator produces a valid testbench.
4. **Display** — the generated testbench appears in the right Monaco pane for copy/download.

## 📄 License

MIT
