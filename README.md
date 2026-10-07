# TrailQuest AI 🌿

> **Hacktoberfest 2026 Challenge — Theme: "Touch Grass"**
> An AI-powered outdoor quest generator that uses open-weight AI (Gemma 3 4B) and SerpApi to encourage users to spend less time on screens and more time exploring real-world outdoor locations.

---

## 📌 Problem & Solution

* **The Problem:** Modern screen addiction keeps people indoors and isolated from nature, leading to sedentary habits.
* **The Solution:** **TrailQuest AI** turns outdoor exploration into a game! Users input their location, available time, preferred activity, difficulty level, and interests. The app fetches **real local outdoor spots** via SerpApi and prompts **Gemma 3 4B (via Ollama)** to craft a personalized outdoor quest. Users complete the quest offline, return, and log their completion status and reflections.

---

## ✨ Features

- 📍 **Real-World Location Search:** Uses SerpApi (Google Maps engine) to discover real parks, gardens, trails, and outdoor areas near the user.
- 🧠 **Gemma 3 4B Integration:** Local open-weight LLM creates custom quests based **STRICTLY** on the real locations returned by SerpApi — no hallucinated or fake locations.
- 🎯 **Structured Quests:** Generates quest title, selected real location, estimated duration, difficulty rating, description, 3–5 actionable objectives, and safety tips.
- 📝 **Quest Reflection & Tracking:** Users can log quest results as `Completed`, `Partially Completed`, or `Not Completed`, along with personal reflections.
- 💾 **MongoDB Atlas Storage:** Stores user preferences, generated quests, completion statuses, and timestamps.
- 📱 **Clean Responsive UI:** Minimalist HTML/CSS/Vanilla JavaScript frontend.

---

## 🏗️ Architecture & Technology Stack

```
   [ Web Frontend (HTML/CSS/JS) ]
                 │
                 ▼
      [ FastAPI Backend (Python) ]
         │                │
         ▼                ▼
   [ SerpApi ]     [ Gemma 3 4B ]
(Real Locations)   (Ollama Local)
         │                │
         └────────┬───────┘
                  ▼
         [ MongoDB Atlas ]
        (Quest & Logs DB)
```

- **Frontend:** HTML5, CSS3 (Vanilla), JavaScript (ES6+)
- **Backend:** Python 3.14, FastAPI, Pydantic, Uvicorn
- **AI Model:** Gemma 3 4B via Ollama
- **Location API:** SerpApi (Google Maps Engine)
- **Database:** MongoDB Atlas (via Motor / AsyncPyMongo with in-memory fallback for offline dev)

---

## 📂 Project Structure

```
TrailQuestAI/
├── backend/
│   └── app/
│       ├── __init__.py
│       ├── config.py             # Environment configuration
│       ├── main.py               # FastAPI application & endpoints
│       ├── database/
│       │   └── mongodb.py        # MongoDB Atlas repository & fallback
│       ├── models/
│       │   └── quest.py          # Pydantic request/response schemas
│       └── services/
│           ├── gemma_service.py   # Ollama API client
│           ├── serpapi_service.py # SerpApi location search client
│           └── quest_service.py   # Quest orchestration & prompt logic
├── frontend/
│   ├── index.html                # Main UI layout
│   ├── style.css                 # Modern responsive styling
│   └── script.js                 # API integration & DOM logic
├── tests/
│   └── test_api.py               # Pytest suite
├── .env.example                  # Environment template
├── requirements.txt              # Python dependencies
├── PROJECT_CONTEXT.md            # Project architecture context
└── TRAILQUEST_MVP_REQUIREMENTS.md# MVP specification
```

---

## 🚀 Local Setup & Installation

### Prerequisites
1. Python 3.10+
2. [Ollama](https://ollama.com/) installed and running locally
3. Pull the Gemma 3 4B model:
   ```bash
   ollama pull gemma3:4b
   ```
4. SerpApi API Key ([Get one free here](https://serpapi.com/))

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mallavarapusudhishna/TrailQuest-AI.git
   cd TrailQuest-AI
   ```

2. **Set up virtual environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .\.venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Create a `.env` file in the project root based on `.env.example`:
   ```env
   SERPAPI_API_KEY=your_serpapi_key_here
   MONGODB_URI=your_mongodb_atlas_uri_here
   ```

5. **Start Ollama service (if not running):**
   ```bash
   ollama serve
   ```

6. **Run the FastAPI server:**
   ```bash
   python -m uvicorn backend.app.main:app --reload
   ```

7. Open your browser at `http://127.0.0.1:8000` to use TrailQuest AI!

---

## 🧪 Running Tests

Automated unit and integration tests mock external API calls to run reliably without consuming live credits:

```bash
python -m pytest
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | API health check |
| `POST` | `/generate-quest` | Accepts preferences, searches locations via SerpApi, prompts Gemma, saves quest to DB |
| `POST` | `/quests/{id}/complete` | Updates quest completion status (`completed`, `partially_completed`, `not_completed`) & reflection |
| `GET` | `/quests/{id}` | Retrieves quest details and completion status by ID |
| `GET` | `/quests` | Lists recent quests |

---

## 🌐 Deployment Notes (Render)

When deploying the MVP to cloud platforms like Render:
1. **Ollama / Gemma model hosting:** Standard Render Web Services run in ephemeral containers without GPU acceleration. For cloud production, point `OLLAMA_URL` in `gemma_service.py` to a hosted Ollama instance (e.g., Modal, Replicate, RunPod, or a cloud VM running Ollama).
2. Set `SERPAPI_API_KEY` and `MONGODB_URI` environment variables in the Render Dashboard.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
