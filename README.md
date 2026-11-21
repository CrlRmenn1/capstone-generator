# CapSense: Capstone Title Recommender

A web app for IT/CS students that suggests capstone titles from the team's program, interests, target domain, difficulty, skills, and keywords, then turns the chosen title into an editable **Chapter 1 draft** for the outline defense, exportable to **Word (DOCX)** or **PDF**.

- **Backend:** Python, Flask JSON API (`app/`)
- **Frontend:** React, Vite, Tailwind CSS (`frontend/`)

## Features
- **Two title sources:** new ideas (template engine, or AI with your own key) plus similar existing capstones from the dataset.
- **Scoring:** 60% relevance to the preferences plus 40% novelty against existing titles; near-duplicates (≥ 0.75 title similarity) are removed.
- **Accounts and saved titles.**
- **Onboarding for new users:** a welcome tour right after sign-up, a getting-started checklist on the home page that ticks itself off as the student finds, saves, develops, and exports, and a Guide page (`/guide`) with instructions, FAQs, and outline-defense tips. Progress is stored per account (`user_progress` table).
- **Chapter 1 drafts:** Background, Statement of the Problem, Objectives (matched one-to-one with the problems), Significance, Scope and Limitations, Definition of Terms, and System Overview. Edit, regenerate, or undo each section. Start from a suggestion or from your own title.
- **Export** to DOCX (Times New Roman 12, double-spaced, 1.5" left margin) or PDF.
- **Bring your own key (optional):** students add their own Claude, OpenAI, or Gemini key. The app never uses a shared key, so heavy use can't block it.
  - The key is kept in server memory only for the current login by default, or stored encrypted (Fernet) if the student chooses "remember".
  - If an AI call fails, the app offers to finish the job in default mode.
- **Protection:** per-user and per-IP rate limits, a CSRF header check, and an "AI cache" so repeated identical requests don't spend a student's quota.

## First-time setup (Windows)
```powershell
# Backend
py -3.13 -m venv .venv            # or the full path to a working Python 3.12/3.13
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Frontend
cd frontend
npm install
npm run build                     # creates frontend/dist, which Flask serves
cd ..
```

## Run it
**Normal use / demo** (one server):
```powershell
.\.venv\Scripts\python.exe run.py
```
Open http://127.0.0.1:5000

**While changing the React code** (live reload), use two terminals:
```powershell
# Terminal 1: API
.\.venv\Scripts\python.exe run.py
# Terminal 2: React dev server (forwards /api to Flask)
cd frontend; npm run dev
```
Open http://localhost:5173

After editing React code, run `npm run build` again so http://127.0.0.1:5000 shows the changes.

## Tests
```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
The AI tests use a fake provider, so no API key or money is needed.

## Data
- **Titles:** import a CSV (`title, abstract, program, area, domain, tags, tech_stack, year, source`) with
  `.\.venv\Scripts\python.exe scripts\import_titles.py path\to\titles.csv`.
  `data/seed_titles.csv` holds **sample titles written for development**. Replace them with real ones (for example, your department's past capstones, with permission) before evaluation.
- **Knowledge base:** `data/knowledge_base/` holds `technologies.json`, `domains.json` (problems, modules, beneficiaries), and `title_patterns.json`. The app validates these files at startup.

## Project layout
```
app/
  api/            JSON endpoints: auth, titles, bookmarks, outlines (+ export), settings (AI keys), meta
  engines/        template_engine (titles), outline_template (Chapter 1), ai_engine (BYOK), context
  ai/providers.py Claude / OpenAI / Gemini adapters behind one generate_json() call
  recommender.py  TF-IDF + cosine similarity over the dataset
  security.py     API-key storage (memory or Fernet-encrypted)
  exporter.py     DOCX / PDF
frontend/src/
  pages/          GeneratePage, SavedPage, OutlinesPage, OutlineEditorPage, SettingsPage, AuthPage
  components/     Layout, TitleCard, Markdown, ui
```
