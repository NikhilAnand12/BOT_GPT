# BOT GPT - Conversational AI 

A conversational AI platform with RAG (Retrieval-Augmented Generation) capabilities.

## Features

- **Open Chat Mode**: General conversation with Groq LLM
- **Grounded/RAG Mode**: Chat with your documents (PDF support)
- **RESTful API**: Full CRUD operations for conversations, messages, and documents
- **Vector Search**: ChromaDB for semantic document retrieval
- **Streamlit UI**: Beautiful, interactive chat interface
- **SQLite Database**: Local, zero-config data persistence

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **LLM**: llama-3.1-8b-instant
- **Embeddings**: HuggingFaceEmbeddings(BAAI/bge-small-en-v1.5)
- **Vector Store**: ChromaDB
- **Database**: SQLite
- **Frontend**: Streamlit
- **LLM Framework**: LangChain

## Project Structure

```
bot-gpt/
├── src/
│   ├── api/
│   │   ├── routes.py          # API endpoints
│   │   └── schemas.py         # Pydantic models
│   ├── models/
│   │   ├── database.py        # Database setup
│   │   └── models.py          # SQLAlchemy models
│   ├── services/
│   │   ├── llm_service.py     # LLM interactions
│   │   ├── document_service.py # RAG and document processing
│   │   └── conversation_service.py # Conversation management
│   ├── config.py              # Configuration
│   └── main.py                # FastAPI app
├── tests/
│   └── test_api.py            # Unit tests
├── docs/                       # Architecture documentation
├── data/                       # SQLite DB, uploads, ChromaDB
├── streamlit_app.py           # Streamlit UI
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables
└── README.md
```

## Installation

### Prerequisites

- Python 3.11 or higher
- pip

### Setup

1. **Clone/Navigate to the project**
```bash
cd bot-gpt
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment variables**

The `.env` file configured with:
- llm API Key
- Database URL
- ChromaDB path
- Upload directory

## Running the Application

### Method 1: Streamlit UI 

1. **Start the FastAPI backend** (in terminal 1):
```bash
cd bot-gpt
python -m uvicorn src.main:app --reload
```

2. **Start the Streamlit UI** (in terminal 2):
```bash
cd bot-gpt
streamlit run streamlit_app.py
```

3. **Open your browser**:
- Streamlit UI: http://localhost:8501
- API Docs: http://localhost:8000/docs

### Method 2: API Only (for Postman/cURL testing)

```bash
cd bot-gpt
python -m uvicorn src.main:app --reload
```

Access the API at: http://localhost:8000


### Using Streamlit UI

1. **Login/Register**: Create a demo account
2. **New Chat**: Click "New Chat" for open conversation
3. **Upload Document**: Upload PDF for RAG mode
4. **RAG Chat**: Select documents and click "Start RAG Chat"
5. **Chat**: Type messages and get responses
6. **Delete**: Remove old conversations

### Using API (Postman/cURL)

#### 1. Create User
```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com"
  }'
```

#### 2. Create Conversation
```bash
curl -X POST http://localhost:8000/api/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER_ID_HERE",
    "title": "Python Discussion",
    "mode": "open_chat",
    "first_message": "What are Python decorators?"
  }'
```

#### 3. Add Message to Conversation
```bash
curl -X POST http://localhost:8000/api/v1/conversations/CONV_ID/messages \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Can you show an example?"
  }'
```

#### 4. Upload Document
```bash
curl -X POST http://localhost:8000/api/v1/documents \
  -F "file=@document.pdf" \
  -F "user_id=USER_ID_HERE"
```

#### 5. Create RAG Conversation
```bash
curl -X POST http://localhost:8000/api/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER_ID_HERE",
    "title": "Questions about Document",
    "mode": "grounded",
    "document_ids": ["DOC_ID_HERE"]
  }'
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/users` | Create user |
| GET | `/api/v1/users/{id}` | Get user |
| POST | `/api/v1/conversations` | Create conversation |
| GET | `/api/v1/conversations` | List conversations |
| GET | `/api/v1/conversations/{id}` | Get conversation details |
| POST | `/api/v1/conversations/{id}/messages` | Add message |
| DELETE | `/api/v1/conversations/{id}` | Delete conversation |
| POST | `/api/v1/documents` | Upload document |
| GET | `/api/v1/documents` | List documents |
| GET | `/api/v1/documents/{id}` | Get document |
| DELETE | `/api/v1/documents/{id}` | Delete document |

### High-Level Flow

```
User → Streamlit UI → FastAPI → Services → Database/ChromaDB
                                    ↓
                              LLM API (LLM + Embeddings)
```

### RAG Pipeline

1. **Document Upload**: PDF → Extract Text → Chunk → Generate Embeddings → Store in ChromaDB
2. **Query**: User Question → Generate Query Embedding → Similarity Search → Retrieve Top Chunks
3. **Generate Response**: Context + History + Query → LLM → Response

### Database Schema

- **Users**: Store user information
- **Conversations**: Track chat sessions (open_chat or grounded mode)
- **Messages**: Store all messages with roles (user/assistant/system)
- **Documents**: Metadata for uploaded PDFs

## Configuration

Edit `.env` to customize:

```env
LLM_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///./data/bot_gpt.db
CHROMADB_PATH=./data/chromadb
UPLOAD_DIR=./data/uploads
```
