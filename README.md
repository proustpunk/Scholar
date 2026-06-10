# Scholara — AI Study Notes & Q&A

Scholara is an AI-powered study tool that turns scanned textbook PDFs into structured notes and lets you ask questions about what you're studying. Upload a book, index its chapters, and let the AI do the reading.

---

## What it does

- **Upload scanned PDFs** — works with photographed or scanned textbooks, not just digital ones
- **Chapter indexing** — tell the system which pages belong to which chapter, once per book
- **AI note generation** — OCR extracts text from the pages, an LLM turns it into clean, structured study notes
- **Ask questions** — RAG-powered Q&A lets you ask anything about a chapter and get answers grounded in the actual content
- **Per-user sessions** — each browser gets its own workspace with persistent history, no login required

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy |
| Database | PostgreSQL |
| OCR | Tesseract via pytesseract, PyMuPDF |
| Embeddings | Sentence Transformers / HuggingFace Inference API |
| Vector store | ChromaDB |
| LLM | Groq (Llama 3.1) |
| RAG pipeline | LangChain |
| Frontend | Jinja2 templates, vanilla JS |
| Deployment | Render |

---

## How it works

```
Upload PDF
    ↓
User indexes chapters (chapter name → page range)
    ↓
User selects a chapter → "Generate Notes"
    ↓
PyMuPDF slices pages → Tesseract OCR → clean text → chunks
    ↓
Chunks stored in ChromaDB (vector embeddings)
    ↓
Groq LLM generates structured notes → saved to PostgreSQL
    ↓
User asks a question
    ↓
LangChain retrieves top matching chunks from ChromaDB
    ↓
Groq LLM answers based on retrieved context
```

---

## Project structure

```
app/
├── api/routes/
│   ├── books.py        # upload, index, process chapters
│   ├── notes.py        # fetch notes
│   └── chat.py         # Q&A and chat history
├── core/
│   ├── database.py     # SQLAlchemy setup
│   ├── config.py       # environment settings
│   └── session.py      # cookie-based user sessions
├── models/             # SQLAlchemy models
├── schemas/            # Pydantic schemas
├── services/
│   ├── pdf_service.py  # OCR pipeline
│   ├── llm_service.py  # Groq note generation
│   ├── rag_service.py  # ChromaDB + LangChain Q&A
│   └── notes_service.py # pipeline orchestrator
templates/
└── index.html          # single-page UI
main.py
```

---

## Local setup

**Requirements:**
- Python 3.11
- PostgreSQL
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) (Windows installer)

**1. Clone and install:**

```bash
git clone https://github.com/yourusername/scholara.git
cd scholara
python -m venv env
env\Scripts\activate        # Windows
pip install -r requirements.txt
```

**2. Create a `.env` file:**

```env
DATABASE_URL=postgresql://youruser:yourpassword@localhost:5432/yourdb
GROQ_API_KEY=your_groq_key
UPLOAD_DIR=uploads
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

**3. Run:**

```bash
uvicorn main:app --reload
```

Visit `http://127.0.0.1:8000`

---

## Environment variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `GROQ_API_KEY` | From [console.groq.com](https://console.groq.com) — free |
| `UPLOAD_DIR` | Folder for uploaded PDFs (default: `uploads`) |
| `TESSERACT_PATH` | Path to Tesseract binary |

---

## Deployment

Designed for [Render](https://render.com). See `render.yaml` for configuration.

> **Note:** Uploaded PDFs and ChromaDB vector data are stored on the local filesystem and will not persist across Render deploys on the free tier. For production use, swap `UPLOAD_DIR` to an S3-compatible bucket and configure persistent ChromaDB storage.

---

## Roadmap

- [ ] Cloud storage for PDFs (S3 / Cloudflare R2)
- [ ] Persistent vector store
- [ ] Email/password authentication
- [ ] Multiple workspaces per user
- [ ] Export notes as PDF
- [ ] Highlight and annotate notes

---

## License

MIT
