# 🏏 CricketIQ AI

**IPL Cricket Intelligence Platform** — Ask any cricket question in plain English and get data-driven answers powered by a hybrid RAG + SQL Agent system.

## 🚀 Live Demo

- **Frontend**: [Streamlit App](https://cricketiq-ai-w7zyqvr3rbraiciwkvnnpz.streamlit.app/)
- **Backend API**: [https://cricketiq-ai.onrender.com](https://cricketiq-ai.onrender.com)
- **API Docs**: [https://cricketiq-ai.onrender.com/docs](https://cricketiq-ai.onrender.com/docs)

> **Note:** The backend runs on Render's free tier and sleeps after 15 minutes of inactivity. The first request after a period of inactivity may take 30-60 seconds while the server wakes up.

---

## 🧠 What It Does

CricketIQ AI routes every question to the right intelligence pipeline automatically:

| Route | Question type | Example |
|---|---|---|
| 🟢 SQL | Statistical / ranking / comparison | "Top 10 run scorers in IPL", "How is Rohit Sharma different from Yuvraj Singh?" |
| 🔵 RAG | Profile / descriptive | "Who is MS Dhoni as a player?" |
| 🟣 HYBRID | Complex / narrative comparisons | "Is Rohit better than Kohli overall?" |

---

## 🏗️ Architecture

```
Question
  -> QueryRewriter       expand abbreviations, fix nicknames, no cascading bugs
  -> EntityExtractor      extract players, venues, phases, teams via regex
  -> IntentRouter         SQL / RAG / HYBRID decision
  -> SQL Agent            LLM generates + validates + executes SQL
  -> RAG Pipeline          FAISS semantic search + LLM narrative generation
  -> HybridComposer       fuses SQL stats + RAG narrative for complex questions
  -> ResultFormatter       canonical names, rich comparison narratives, chart hints
  -> Answer
```

**Stack:**
- **Backend**: FastAPI + SQLAlchemy + SQLite (production) / MySQL (local dev)
- **LLM**: Groq (`openai/gpt-oss-120b` for hybrid reasoning, `openai/gpt-oss-20b` for RAG)
- **Vector Store**: FAISS + HuggingFace Inference API (`all-MiniLM-L6-v2`, 384-dim)
- **Frontend**: Streamlit
- **Data**: IPL ball-by-ball from Cricsheet, full tournament history including IPL 2009 (South Africa) and IPL 2014/2020 (UAE) seasons

---

## 📊 Dataset

- **1,235 IPL matches** (2008-2024, all 19 historical franchises)
- **293,764 ball-by-ball records**
- **805 unique players**, fully canonicalized (DB shortcodes to full names)
- **733 batters, 577 bowlers** with detailed career statistics
- **445 players** with AI-generated intelligence profiles (batters, bowlers, and genuine all-rounders; qualification requires either 100+ runs or 15+ wickets)
- **60 venues** classified as Batting Friendly / Balanced / Bowling Friendly using percentile-based thresholds relative to the actual run-rate distribution

---

## 🛠️ Local Development

### Prerequisites
- Python 3.11+
- MySQL 8.0+ (for local development; production uses a pre-built SQLite file)
- Groq API key (free at console.groq.com)
- HuggingFace token (free at huggingface.co/settings/tokens), used for embeddings via Inference API

### Setup

```bash
# Clone
git clone https://github.com/garvchanana/cricketiq-ai.git
cd cricketiq-ai

# Backend
cd backend
python -m venv venv
venv\Scripts\activate     # Windows
pip install -r requirements.txt

# Copy env template and fill in your credentials
cp .env.example .env

# Start backend (local MySQL mode)
$env:USE_SQLITE="false"   # PowerShell, omit or set "true" to use bundled SQLite instead
uvicorn app.main:app --reload
```

```bash
# Frontend (new terminal)
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

### Environment Variables

```env
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=cricketiq_ai
GROQ_API_KEY=gsk_your_key
HF_TOKEN=hf_your_token
LOG_LEVEL=INFO
USE_SQLITE=false
```

---

## 🧪 Testing

```bash
cd backend
python -m pytest tests/ -v
```

Full test suite covering SQL safety (injection, destructive statements, CTE support), SQL generation regression guards, NLP retrieval, API endpoints, and full end-to-end integration, 100+ tests.

---

## 📁 Project Structure

```
cricketiq-ai/
├── backend/
│   ├── app/
│   │   ├── agents/          SQL Agent, Intent Router, Hybrid Composer
│   │   ├── analytics/       Player, Match, Matchup, Final Answer agents
│   │   ├── api/             FastAPI routes + dependencies
│   │   ├── core/            Config, logging, security (CORS, rate limiting)
│   │   ├── database/        Models + dual MySQL/SQLite session
│   │   ├── llm/              Groq client + prompt builder + response generator
│   │   ├── nlp/               Canonicalization (805-name registry), rewriter, entity extraction
│   │   ├── rag/               FAISS store + retrieval + RAG chains
│   │   └── services/         Feature engineering (batting, bowling, rankings, intelligence, venues)
│   ├── tests/                Full test suite
│   ├── data/faiss_index/     Persisted FAISS index (loaded on startup, not rebuilt)
│   └── requirements.txt
├── frontend/
│   ├── pages/                6 Streamlit pages
│   ├── services/             API client (points to live Render backend)
│   ├── utils/                 Formatters + shared 805-name player registry
│   ├── app.py
│   └── requirements.txt
├── cricketiq.db               Pre-built production SQLite (committed for Render free-tier persistence)
├── Dockerfile
├── render.yaml
└── README.md
```

---

## 🔌 API Endpoints

| Endpoint | Description |
|---|---|
| `GET /ask?question=...` | Unified ask, SQL/RAG/HYBRID auto-routing |
| `GET /ask/route?question=...` | Debug routing decision without executing |
| `GET /agent/sql/ask?question=...` | SQL agent only |
| `GET /agent/sql/execute?sql=...` | Direct SQL execution (raw DB shortcode names, by design) |
| `GET /agent/sql/validate?sql=...` | SQL safety validation only |
| `GET /rag/ask?query=...` | RAG pipeline only |
| `GET /docs` | Interactive Swagger UI |

---

## 🖥️ Frontend Pages

| Page | Purpose |
|---|---|
| **Chat** | Conversational Q&A across all routes |
| **Player Search** | Full player profiles: intelligence, batting, bowling, matchups |
| **Compare** | Side-by-side comparison with AI narrative and stat charts |
| **Analytics** | Natural language or Direct SQL explorer, including CTE support |
| **Rankings** | Filterable leaderboard (Batter / Bowler / All-Rounder) |
| **Venues** | Venue statistics with Batting/Bowling/Balanced classification |

---

## 🔍 Engineering Highlights

A few things worth knowing about how this was built:

- **Player name canonicalization** — an 805-entry registry maps every Cricsheet DB shortcode (e.g. "V Kohli") to its full canonical name ("Virat Kohli"), used consistently across RAG, SQL narrative generation, and frontend display, while raw debug endpoints intentionally preserve DB format for transparency.
- **Hybrid routing** — an intent router classifies every question as SQL, RAG, or HYBRID based on extracted entities and question structure, not just keyword matching.
- **Production-safe SQL generation** — every LLM-generated query passes through a validator that blocks destructive statements, enforces read-only access, and restricts table access to a safe schema subset.
- **Memory-optimized deployment** — embeddings are generated via the HuggingFace Inference API rather than a locally-loaded PyTorch model, keeping the deployed backend under 100MB RAM to fit Render's free tier.
- **Deployment-persistent FAISS index** — the vector index is built once, saved to disk, and loaded on subsequent startups rather than rebuilt on every deploy.

---

## 🗺️ Roadmap

- [ ] T20 International data expansion
- [ ] Women's IPL (WPL) data
- [ ] Real-time match commentary integration
- [ ] Multi-language support

---

Built with FastAPI, Groq, FAISS, and Streamlit.

---

# Author

Garv Chanana