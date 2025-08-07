from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from pathlib import Path
import shutil
from fastapi import HTTPException
from difflib import SequenceMatcher
import os

# Load environment variables
load_dotenv()

# Directories
UPLOAD_FOLDER = Path("data")
INDEX_DIR = "faiss_index"
UPLOAD_FOLDER.mkdir(exist_ok=True)
Path(INDEX_DIR).mkdir(exist_ok=True)

# FastAPI app setup
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global chain, memory, retriever
llm = GoogleGenerativeAI(model="gemini-2.5-flash")

custom_prompt = PromptTemplate(
    input_variables=["chat_history", "question", "context"],
    template="""
You are a helpful assistant answering questions from a document.
Try to stick to the provided context.
If the question is irrelevant or outside the document, politely respond:
"I'm only trained to answer questions based on the document content."
If asked who created or trained you, reply with:
"Hashir made me" or something similar.

Context:
{context}

Chat History:
{chat_history}

User Question:
{question}

Answer:
"""
)

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key="answer")

def process_all_pdfs():
    """Load all PDFs, split, embed and return a FAISS vectorstore"""
    all_docs = []
    for pdf_file in UPLOAD_FOLDER.glob("*.pdf"):
        loader = PyPDFLoader(str(pdf_file))
        all_docs.extend(loader.load())

    if not all_docs:
        return None

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(all_docs)

    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(INDEX_DIR)

    return vectorstore

def clean_faiss_index(db, embeddings):
    """Remove indexed data from deleted files"""
    # Get existing PDFs in the upload folder
    existing_files = set(str(p.resolve()) for p in UPLOAD_FOLDER.glob("*.pdf"))

    # Get all docs from FAISS index
    all_docs = db.similarity_search(".")

    # Keep only those whose source file still exists
    valid_docs = [
        doc for doc in all_docs
        if Path(doc.metadata.get("source", "")).resolve().__str__() in existing_files
    ]
    if not valid_docs:
        print("No valid documents found to build the FAISS index.")
        return db  # Or return None

    if len(valid_docs) < len(all_docs):
        print("🧹 Some documents were deleted. Rebuilding FAISS without them...")
        db = FAISS.from_documents(valid_docs, embeddings)
        db.save_local(INDEX_DIR)

    return db

def create_qa_chain():
    """Create or rebuild the QA chain with FAISS cleanup"""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    faiss_path = Path(INDEX_DIR, "index.faiss")

    if not faiss_path.exists():
        print("⚠️ No FAISS index found.")
        return None

    db = FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
    db = clean_faiss_index(db, embeddings)  # Clean up deleted sources

    retriever = db.as_retriever()
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": custom_prompt},
        return_source_documents=True,
    )

# Initialize QA chain on startup
qa_chain = create_qa_chain()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = UPLOAD_FOLDER / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Rebuild the FAISS index and reload chain
    vectorstore = process_all_pdfs()
    global qa_chain
    qa_chain = create_qa_chain()

    return {"filename": file.filename, "status": "✅ Uploaded and indexed"}

@app.get("/files")
async def list_uploaded_files():
    """List current PDFs in the /data folder"""
    files = [f.name for f in UPLOAD_FOLDER.glob("*.pdf")]
    return {"files": files}

class Query(BaseModel):
    question: str





@app.post("/query")
async def ask_question(query: Query):
    global qa_chain
    if qa_chain is None:
        return {"answer": "No documents found. Please upload a PDF first."}

    print(f"🔍 Received: {query.question}")
    result = qa_chain.invoke({"question": query.question})

    answer = result.get("answer", "")
    source_docs = result.get("source_documents", [])

    # ✅ Check if sources are truly relevant using simple heuristic
    relevant_sources = []
    for doc in source_docs:
        content = doc.page_content
        similarity = SequenceMatcher(None, content.lower(), answer.lower()).ratio()

        # Heuristic: Only include if answer is at least 15% similar to source content
        if similarity >= 0.13:
            metadata = doc.metadata
            source = metadata.get('source', 'Unknown')
            if(source not in relevant_sources):
                relevant_sources.append(f"{Path(source).name}")

    # ✅ Final answer string with or without sources
    if relevant_sources:
        source_str = ", ".join(relevant_sources)
        answer += f"\n\n📚 Sources: {source_str}"
    else:
        answer += "\n\n📚 Sources: None found or FAISS is currently Processing (possibly AI's own knowledge)."

    return {"answer": answer}


