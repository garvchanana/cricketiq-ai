# 🏏 CricketIQ AI

**IPL Cricket Intelligence Platform** — Ask any cricket question in plain English and get data-driven answers powered by a hybrid RAG + SQL Agent system.

## 🚀 Live Demo

- **Frontend**: [Streamlit App](https://your-app.streamlit.app) *(update after deployment)*
- **Backend API**: [Render API](https://cricketiq-ai.onrender.com) *(update after deployment)*
- **API Docs**: [Swagger UI](https://cricketiq-ai.onrender.com/docs)

---

## 🧠 What It Does

CricketIQ AI routes every question to the right intelligence pipeline:

| Route | Question type | Example |
|---|---|---|
| 🟢 SQL | Statistical / ranking | "Top 10 run scorers in IPL" |
| 🔵 RAG | Profile / descriptive | "Who is MS Dhoni as a player?" |
| 🟣 HYBRID | Complex / comparative | "Is Rohit better than Kohli?" |

---

## 🏗️ Architecture

```
Question
  → QueryRewriter     — expand abbreviations, fix nicknames
  → EntityExtractor   — extract players, venues, phases
  → IntentRouter      — SQL / RAG / HYBRID decision
  → SQL Agent         — LLM generates + validates + executes SQL
  → RAG Pipeline      — FAISS semantic search + Groq LLM
  → HybridComposer    — fuses SQL stats + RAG narrative
  → Answer
```

**Stack:**
- **Backend**: FastAPI + SQLAlchemy + MySQL
- **LLM**: Groq (llama3-70b-8192 + llama-3.1-8b-instant)
- **Vector Store**: FAISS + HuggingFace sentence-transformers
- **Frontend**: Streamlit
- **Data**: IPL ball-by-ball from Cricsheet (1235 matches, 293,764 deliveries)

---

## 📊 Dataset

- **1,235 IPL matches** (2008–2026, all franchises)
- **293,764 ball-by-ball records**
- **733 batters, 577 bowlers**
- **19 IPL teams** (all historical franchises)
- **331 player intelligence profiles** (AI-generated summaries)

---

## 🛠️ Local Development

### Prerequisites
- Python 3.11+
- MySQL 8.0+
- Groq API key (free at groq.com)

### Setup

```bash
# Clone
git clone https://github.com/yourusername/cricketiq-ai.git
cd cricketiq-ai
python -m venv venv
venv\Scripts\Activate  # Windows
# Backend
cd backend
pip install -r requirements.txt

# Copy env template
cp .env.example .env
# Edit .env with your credentials

# Start backend
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
MYSQL_DATABASE=cricketiq
GROQ_API_KEY=gsk_your_key
HF_TOKEN=hf_your_token  # optional
LOG_LEVEL=INFO
```

---

## 🧪 Testing

```bash
cd backend
python -m pytest tests/ -v
```

Test suite: 100+ tests across SQL safety, generation, retrieval, API endpoints, and integration.

---

## 📁 Project Structure

```
cricketiq-ai/
├── backend/
│   ├── app/
│   │   ├── agents/          # SQL Agent + Intent Router + Hybrid Composer
│   │   ├── analytics/       # Player, Match, Matchup, Final Answer agents
│   │   ├── api/             # FastAPI routes + dependencies
│   │   ├── core/            # Config, logging, security
│   │   ├── database/        # Models + session
│   │   ├── llm/             # Groq client + prompt builder
│   │   ├── nlp/             # Canonicalization + rewriter + entity extraction
│   │   ├── rag/             # FAISS store + retrieval + RAG chains
│   │   └── services/        # Feature engineering services
│   ├── tests/               # Full test suite (Phase 10)
│   └── requirements.txt
├── frontend/
│   ├── pages/               # 6 Streamlit pages
│   ├── services/            # API client
│   ├── utils/               # Formatters
│   ├── app.py               # Main Streamlit app
│   └── requirements.txt
├── Dockerfile
├── render.yaml
└── README.md
```

---

## 🔌 API Endpoints

| Endpoint | Description |
|---|---|
| `GET /ask?question=...` | Unified ask — SQL/RAG/HYBRID auto-routing |
| `GET /ask/route?question=...` | Debug routing decision |
| `GET /agent/sql/ask?question=...` | SQL agent only |
| `GET /agent/sql/execute?sql=...` | Direct SQL execution |
| `GET /rag/ask?query=...` | RAG pipeline only |
| `GET /docs` | Swagger UI |

---

## 🗺️ Roadmap

- [ ] T20 International data expansion
- [ ] Women's IPL (WPL) data
- [ ] Real-time match commentary integration
- [ ] React frontend with advanced charts
- [ ] Multi-language support

---

## 📝 Author

Garv Chanana

---