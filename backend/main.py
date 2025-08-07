from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
import os
from fastapi import UploadFile, File
from pathlib import Path
import shutil
from langchain_text_splitters import RecursiveCharacterTextSplitter


# Load environment variables
load_dotenv()

# Paths
PDF_PATH = "data/"
INDEX_DIR = "faiss_index"

# FastAPI app
app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load or create FAISS vectorstore
def load_or_create_vectorstore():
    if os.path.exists(f"{INDEX_DIR}/index.faiss"):
        print("🔁 Loading existing FAISS index...")
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        return FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
    else:
        print("📄 Loading PDF and creating vectorstore...")
        loader = PyPDFLoader(PDF_PATH)
        docs = loader.load()
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        db = FAISS.from_documents(docs, embeddings)
        db.save_local(INDEX_DIR)
        return db

# Initialize components
vectorstore = load_or_create_vectorstore()
retriever = vectorstore.as_retriever()
llm = GoogleGenerativeAI(model="gemini-2.5-flash")

# Custom prompt to control LLM behavior
custom_prompt = PromptTemplate(
    input_variables=["chat_history", "question", "context"],
    template="""
You are a helpful assistant answering questions from a document.
try stick to the context provided.
If the question is irrelevant or outside the document, politely respond: 
"I'm only trained to answer questions based on the document content." or any other similar answer
and if ever someone asks you who trained you or who owns you respond Hashir made me or similar like this

Context:
{context}

Chat History:
{chat_history}

User Question:
{question}

Answer:
"""
)

# Add memory to store chat history
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# Create Conversational RAG chain
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key="answer")

qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever,
    memory=memory,
    combine_docs_chain_kwargs={"prompt": custom_prompt},
    return_source_documents=True,
)

UPLOAD_FOLDER = Path("data")  # where your PDFs will go

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = UPLOAD_FOLDER / file.filename

    # Save uploaded PDF
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Refresh retriever with updated data
    global retriever
    retriever = process_all_pdfs().as_retriever()

    return {"filename": file.filename, "status": "uploaded and indexed"}



def process_all_pdfs():
    docs = []
    
    for file in UPLOAD_FOLDER.glob("*.pdf"):
        loader = PyPDFLoader(str(file))
        docs.extend(loader.load())
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(docs)

    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local("faiss_index")  # Optional

    return vectorstore


# Request body model
class Query(BaseModel):
    question: str

# Endpoint to ask questions
@app.post("/query")
async def ask_question(query: Query):
    print(f"🔍 Received: {query.question}")
    result = qa_chain.invoke({"question": query.question})

    # Extract sources
    sources = []
    for doc in result.get("source_documents", []):
        metadata = doc.metadata
        source_info = f"{metadata.get('source', 'Unknown')} - Page {metadata.get('page', '?')}"
        sources.append(source_info)

    
    # Join sources into a readable string
    source_string = ", ".join(sources)

    # Append the sources directly to the answer
    answer_with_sources = f"{result.get('answer')}\n\n📚 Sources: {source_string}"

    return {
        "answer": answer_with_sources
    }
