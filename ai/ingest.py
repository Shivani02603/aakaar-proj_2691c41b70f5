import os
import tempfile
from fastapi import UploadFile
from pypdf import PdfReader
import tiktoken
from .embeddings import get_embedding

def chunk(text: str, chunk_size: int = 1000, chunk_overlap: int = 200):
    enc = tiktoken.get_encoding('cl100k_base')
    tokens = enc.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)
        start += chunk_size - chunk_overlap
    return chunks

async def ingest_pdf(file: UploadFile, session_id: str, user_id: str):
    contents = await file.read()
    original_filename = file.filename or "unknown.pdf"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_filename)[1])
    tmp.write(contents)
    tmp.flush()
    file_path = tmp.name

    try:
        reader = PdfReader(file_path)
        all_chunks = []
        for page_number, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                chunks = chunk(text)
                for i, chunk_text in enumerate(chunks):
                    metadata = {
                        'source_filename': original_filename,
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'page_or_row': f"Page {page_number + 1}"
                    }
                    embedding = get_embedding(chunk_text)
                    all_chunks.append((chunk_text, embedding, metadata))
        return all_chunks
    finally:
        os.unlink(file_path)