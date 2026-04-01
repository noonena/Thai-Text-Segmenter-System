
## Assistant (Build · gpt-5.2 · 24.4s)

The repo’s own README is minimal; the results/README docs describe directory structures that don’t seem implemented. I’m going to draft the project brief now, explicitly calling out these mismatches and any unknowns.

# ThaiTextSegmentersystem Project Brief

## 1) Project Overview

Thai text segmentation system with a web UI.

- Backend: Python FastAPI app providing authentication (cookie sessions) + NLP endpoints (CRF models + Viterbi segmentation) + basic stats/evaluation runner.
- Frontend: React + TypeScript + Vite + Tailwind UI for processing text/HTML, viewing history/stats, and admin user/role management.

Primary backend endpoints live under `/api/*` and require a valid session cookie for most operations.

⚠️ Repo contains several “guide” docs that don’t match current runtime behavior (see Caveats).

---

## 2) File Structure

```text
backend/
  main.py                      # uvicorn entrypoint
  app.py                       # FastAPI app, CORS, CSP/security headers, routers, session cleanup
  requirements.txt             # backend dependencies
  utils/database.py            # SQLite schema/init, default admin, sessions, auth deps
  routers/
    auth.py                    # /api/auth/*
    users.py                   # /api/users/* (admin)
    roles.py                   # /api/roles/* (admin)
    nlp.py                     # /api/nlp/* (auth)
    stats.py                   # /api/statistics* (auth)
  scripts/
    nlp_utils/                 # ThaiTextSegmenter pipeline, Viterbi, evaluation
    trainers/                  # training scripts for CRF models + dictionary builder
  models/                      # required runtime .pkl artifacts
  data/                        # corpora (LST20 etc)
  results/                     # evaluation JSON outputs (used by /api/statistics)
  database/users.db            # SQLite db file location (created locally)

frontend/
  package.json                 # Vite scripts + deps
  vite.config.ts               # Vite config
  eslint.config.js             # ESLint flat config
  .env.example                 # VITE_API_BASE example
  src/
    main.tsx                   # app bootstrap
    App.tsx                    # routes/tabs + providers
    contexts/AuthContext.tsx   # session verification + authFetch wrapper
    contexts/ProcessingContext.tsx
    pages/                     # ProcessHtml/Text, History, Statistics, Settings, Admin pages
    config/api.ts              # dynamic API discovery (not used by most pages today)
```

---

## 3) Dev Flows (commands only)

Backend (run API):

```bash
python backend/main.py
```

Frontend (run UI):

```bash
cd frontend
npm install
npm run dev
```

Frontend lint/build:

```bash
cd frontend
npm run lint
npm run build
```

Backend evaluation (writes results JSON consumed by stats API):

```bash
python backend/scripts/nlp_utils/evaluate_pipeline.py
```

Model training scripts (examples; see `backend/scripts/trainers/` for others):

```bash
python backend/scripts/trainers/pos_tagger_trainer.py --modified-corpus
python backend/scripts/trainers/syllable_trainer.py
python backend/scripts/trainers/crf_mtu_trainer.py
```

---

## 4) Environment & Config

Frontend env:

- `VITE_API_BASE` (used broadly in UI code)
  - Example (from `frontend/.env.example`):
    - `VITE_API_BASE=http://localhost:8000/api`

Backend runtime details (from code, not a config file):

- Session cookie name: `session` (httpOnly, samesite=lax, `secure=False`, `max_age=1800`)
- SQLite DB path: `backend/database/users.db`
- CORS allows localhost origins (several ports) and credentials.
- CSP/security headers are set in middleware in `backend/app.py`.

⚠️ `frontend/API_CONFIG_GUIDE.md` describes `VITE_AUTH_API` / `VITE_NLP_API` and a centralized `services/api.ts`, but the current code primarily uses `VITE_API_BASE` and does not appear to use a `services/api.ts` client.

---

## 5) Architecture Notes

Backend:

- FastAPI app in `backend/app.py` with routers:
  - `/api/auth/*`: login/logout/verify; session cookie issuance
  - `/api/users/*`, `/api/roles/*`: admin management
  - `/api/nlp/*`: text/HTML processing and training export
  - `/api/statistics*`: reads JSON results; can trigger evaluation script
- NLP pipeline:
  - Singleton `ThaiTextSegmenter` loaded lazily in `backend/routers/nlp.py`
  - Loads pickled artifacts from `backend/models/*.pkl`
  - Uses CRF-based segmentation components + Viterbi for word segmentation/POS.

Frontend:

- Auth is cookie-session based (`credentials: 'include'` on fetches).
- UI stores history in `localStorage` (max 50 entries).
- Role permissions are hardcoded on the frontend in `AuthContext`.

---

## 6) Caveats & Non-Obvious Patterns

⚠️ Port / docs mismatch:
- `backend/main.py` prints a docs URL for `:8002` but actually runs on port `8000`.

⚠️ CSP may block cross-origin frontend calls:
- `backend/app.py` sets a CSP with `connect-src 'self'`, which can block browser fetch/XHR from a different origin/port unless the frontend is same-origin or CSP is adjusted.

⚠️ Default admin credentials and startup behavior:
- `backend/utils/database.py` creates a default admin user `admin/admin123` and clears sessions on startup.

⚠️ Import path manipulation:
- NLP router mutates `sys.path` to import from `backend/scripts/nlp_utils`.

⚠️ Documentation mismatch:
- `backend/results/README.md` and `frontend/results/README.md` describe directory structures/cleanup that are not reflected in the current backend/frontend code paths.

---

## 7) Code Style & Conventions

Frontend:

- TypeScript strict mode is enabled (`noUnusedLocals`, `noUnusedParameters` true).
- ESLint flat config with React Hooks rules and React Refresh plugin (`frontend/eslint.config.js`).
- Tailwind CSS is used for styling.

Backend:

- FastAPI + Pydantic schemas under `backend/schemas/`.
- SQLite access via `sqlite3` in `backend/utils/database.py` (not an ORM).

---

## 8) Testing Approach

- No obvious automated backend test suite (no `pytest.ini` / `pyproject.toml` test config found).
- A manual test script exists: `test/test_model/test_mtu.py` (CLI-style model debug).

---

## 9) Contribution & Git Workflow (if detectable)

- Git remote: `origin https://github.com/noonena/ThaitextSegmentersystem.git`
- Branch: `main` tracking `origin/main`
- No `.github/` CI workflows, `CONTRIBUTING*`, or `LICENSE*` files detected in this workspace snapshot.

---

## 10) Anything Else Worth Knowing (optional)

- There’s an untracked lockfile: `frontend/pnpm-lock.yaml` (repo otherwise appears npm-oriented via `package.json` scripts).

---

