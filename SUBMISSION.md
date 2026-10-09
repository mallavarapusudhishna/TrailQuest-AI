# TrailQuest AI — Hacktoberfest 2026 Week 1 Submission

## A. Project summary

TrailQuest AI is a web app that creates **one personalized outdoor quest** from your city, time budget, activity, difficulty, and interests. It uses **SerpApi** for real places and **Gemma 3 4B through Ollama** for personalization, then gets out of your way so you can go outside and log the result when you return.

## B. Problem

Screen time is easy; getting outside with a concrete plan is harder. People need a **short, trustworthy nudge**— tied to **real locations**—not another feed to scroll.

## C. Solution

1. You enter preferences on a single page.
2. The backend finds real outdoor locations near you.
3. Gemma drafts one quest using **only** those locations.
4. Python validates the JSON and rejects locations not in the search results.
5. The quest is stored (MongoDB or in-memory) and displayed briefly.
6. After your outing, you record completion and an optional reflection.

## D. Why open innovation matters

- **Local inference:** Ollama can run Gemma on your hardware, so quest text generation does not depend on a closed commercial inference API.
- **Transparency:** Prompts and validation logic are in this repo; you can adapt them within license constraints.
- **Replaceability:** `OLLAMA_MODEL` and `OLLAMA_URL` allow swapping to another compatible open-weight model.
- **Privacy nuance:** Prompts sent to **local** Ollama stay on your machine during inference. **SerpApi** still receives location queries, and **MongoDB** may store quests if configured—this is not fully offline privacy.
- **Access:** Open-weight models lower the barrier to experimenting with AI features without mandatory paid LLM API keys for the core quest step.

Trade-off: you (or your host) must run and maintain inference infrastructure; that is the cost of control.

## E. Technical implementation

| Component | Role |
| --- | --- |
| **FastAPI** | REST API, validation, error handling, static frontend |
| **SerpApi** | Google Maps search for parks, gardens, trails, etc. |
| **Ollama + Gemma** | Generates structured quest JSON from preferences + location list |
| **Quest service** | Prompting, JSON extraction, 3–5 objectives, location matching |
| **MongoDB Atlas** | Persistent quests; in-memory fallback when URI is missing |
| **Frontend** | Single-page flow: generate → go outside → complete |

## F. Relevance to “Touch Grass”

The UI is intentionally small: no feeds, maps, leaderboards, or social loops. Copy tells you when the quest is ready and encourages closing the loop quickly. Completion messages are supportive, not guilt-driven. The “Why open-weight AI?” section is informational, not a reason to stay online.

## G. Technical challenges (encountered in this project)

- **Small models and JSON:** Gemma sometimes wraps JSON in markdown; the parser strips fences and validates strictly.
- **Location hallucination:** Even with instructions, models may pick invalid names; server-side matching against SerpApi results rejects invented places.
- **Deployment vs local Ollama:** Cloud hosts cannot call `127.0.0.1` on a developer laptop—documented as Option A (local demo) unless a remote Ollama endpoint is provided.
- **MongoDB optional:** In-memory fallback keeps development and tests working without Atlas.

## H. Limitations

- SerpApi requires network access and an API key.
- Ollama must be running locally (or at a configured remote URL) with sufficient RAM for the model.
- Opening hours, safety, and accessibility of venues are **not** verified.
- CPU-only inference can be slow (tens of seconds to a few minutes).
- Render’s free tier is not assumed to run Gemma 3 4B reliably.

## I. Demo instructions (for judges)

1. Install Python 3.10+, Ollama, and clone this repository.
2. `python -m venv .venv` → activate → `pip install -r requirements.txt`
3. Copy `.env.example` to `.env`; set `SERPAPI_API_KEY` (and optionally `MONGODB_URI`).
4. `ollama pull gemma3:4b` and ensure Ollama is running.
5. `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000`
6. Open `http://127.0.0.1:8000`
7. Try: Location **Chennai**, **60** minutes, **walking**, **easy**, interests **nature, photography**
8. Generate a quest, then submit **Completed** with a short reflection.
9. Run `python -m pytest tests/ -v` to see mocked integration tests.

## J. Short project post (draft)

**TrailQuest AI — Touch Grass with open-weight AI**

I built TrailQuest AI for Hacktoberfest 2026: one real outdoor quest from your city and schedule, powered by **Gemma via Ollama** and **real places from SerpApi**—not invented parks. The app is designed to be the *shortest* part of your day: generate, go outside, come back and log it. Open-weight inference keeps quest generation off closed commercial LLM APIs when you run locally. `#Hacktoberfest` `#OpenSource` `#TouchGrass`

---

*Submission prepared for review; not auto-published.*
