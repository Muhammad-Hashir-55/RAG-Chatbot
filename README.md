# 🤖 RAG AI Assistant

A powerful **Retrieval-Augmented Generation (RAG)** chatbot that accepts PDF files, processes them with LangChain and Gemini, and answers questions based on the uploaded content.

- ⚡ Built with **Next.js** (Frontend)
- 🧠 Powered by **LangChain + Gemini** (Backend)
- 📄 Supports PDF Uploads
- 🔎 FAISS-based Vector Search
- 🧠 Agentic-style querying with source context

---

## 🧱 Tech Stack

| Layer       | Technology         |
|-------------|--------------------|
| Frontend    | Next.js, Tailwind CSS |
| Backend     | FastAPI (Python)    |
| AI Engine   | Google Gemini via LangChain |
| Embedding   | Gemini Embeddings or OpenAI (optional) |
| Vector Store| FAISS              |
| File Support| PDF via PyMuPDF or PyPDFLoader |
| Deployment  | Vercel (Frontend) + Render/Railway (Backend) |

---

## 🖼️ Features

- 📤 Upload PDF files
- 💬 Ask questions from uploaded PDFs
- 📚 RAG with chunking + embedding + vector DB
- 🤖 Gemini-powered answers
- 📎 Source tracking for transparency

---


---

## 🧠 How It Works

1. User uploads a PDF → stored in `/data`
2. Backend processes it:
   - Extracts text
   - Chunks using `RecursiveCharacterTextSplitter`
   - Embeds chunks
   - Stores vectors in FAISS
3. User asks a question
4. Backend retrieves top-k chunks
5. Sends question + context to Gemini
6. Gemini responds, optionally with source

---

## 📦 Setup Instructions
## 🔐 API Key Setup

Before running the backend, make sure to set up your API key to authenticate with the Gemini API (or any LLM you're using).

### ✅ For Gemini (Google Generative AI)

1. Visit: [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2. Generate your API key.
3. Add it to your environment using one of the methods below:

#### On Linux/macOS:
```bash
export GOOGLE_API_KEY=your_api_key_here


### Backend (Python)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

```
### for Frontend
```bash
cd frontend
npm install
npm run dev
```

---

Demo Link: https://ask-pdf-two.vercel.app/