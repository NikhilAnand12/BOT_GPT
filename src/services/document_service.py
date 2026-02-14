"""Document Service for PDF processing and RAG."""

import os
import shutil
from typing import List, Dict
from pathlib import Path
import PyPDF2
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
import chromadb
from chromadb.config import Settings as ChromaSettings
from src.config import settings
from src.models.models import Document


class DocumentService:
    """Service for document processing and RAG."""

    def __init__(self):
        """Initialize document service."""
        # Initialize embeddings with BGE model (free, local)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=settings.chromadb_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )

        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="all_documents",
            metadata={"hnsw:space": "cosine"}
        )

        # Text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
            length_function=len,
        )

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF."""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {page_num + 1} ---\n{page_text}"
        except Exception as e:
            raise Exception(f"Error extracting PDF text: {str(e)}")

        if not text.strip():
            raise Exception("No text could be extracted from PDF")

        return text

    async def process_document(self, file_path: str, document: Document) -> int:
        """Process document: extract text, chunk, embed, and store in ChromaDB."""
        # Extract text
        text = self.extract_text_from_pdf(file_path)

        # Split into chunks
        chunks = self.text_splitter.split_text(text)

        if not chunks:
            raise Exception("No chunks created from document")

        # Prepare metadata for each chunk
        metadatas = []
        ids = []
        for i, chunk in enumerate(chunks):
            metadatas.append({
                "document_id": document.id,
                "chunk_index": i,
                "document_title": document.filename,
                "created_at": document.created_at
            })
            ids.append(f"{document.id}_chunk_{i}")

        # Generate embeddings (batch)
        embeddings = self.embeddings.embed_documents(chunks)

        # Store in ChromaDB
        self.collection.add(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

        return len(chunks)

    async def retrieve_relevant_chunks(
        self,
        query: str,
        document_ids: List[str],
        top_k: int = None
    ) -> List[Dict]:
        """Retrieve relevant chunks for a query."""
        if top_k is None:
            top_k = settings.top_k_chunks

        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)

        # Build where filter
        where_filter = None
        if document_ids:
            where_filter = {"document_id": {"$in": document_ids}}

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        # Format results
        retrieved_chunks = []
        if results and results['documents'] and results['documents'][0]:
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                # Convert distance to similarity score (cosine similarity: 1 - distance)
                similarity = 1 - distance

                # Filter by similarity threshold
                if similarity >= settings.similarity_threshold:
                    retrieved_chunks.append({
                        "content": doc,
                        "metadata": metadata,
                        "similarity_score": similarity,
                        "rank": i + 1
                    })

        return retrieved_chunks

    def format_rag_context(self, chunks: List[Dict]) -> str:
        """Format retrieved chunks into context string."""
        if not chunks:
            return ""

        context_parts = []
        for chunk in chunks:
            metadata = chunk['metadata']
            source = f"[Source: {metadata.get('document_title', 'Unknown')}]"
            context_parts.append(f"{source}\n{chunk['content']}\n")

        return "\n".join(context_parts)

    async def delete_document_chunks(self, document_id: str):
        """Delete all chunks for a document from ChromaDB."""
        try:
            # Get all chunk IDs for this document
            results = self.collection.get(
                where={"document_id": document_id},
                include=[]
            )

            if results and results['ids']:
                # Delete chunks
                self.collection.delete(ids=results['ids'])
        except Exception as e:
            print(f"Error deleting document chunks: {str(e)}")

    async def save_uploaded_file(self, file, user_id: str) -> tuple:
        """Save uploaded file to disk."""
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{user_id}_{file.filename}"
        file_path = os.path.join(settings.upload_dir, unique_filename)

        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Get file size
        file_size = os.path.getsize(file_path)

        return file_path, file_size
