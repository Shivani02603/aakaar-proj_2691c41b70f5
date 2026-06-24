import os
from .embeddings import get_embedding
import openai
from pgvector import VectorStore

async def retrieve_context(query: str, top_k: int, session_id: str, user_id: str):
    embedding = get_embedding(query)
    vector_store = VectorStore()
    results = vector_store.search(embedding, top_k=top_k, session_id=session_id, user_id=user_id)
    return results

async def answer_question(query: str, session_id: str, user_id: str) -> dict:
    context_chunks = await retrieve_context(query, top_k=5, session_id=session_id, user_id=user_id)
    context_texts = [chunk['text'] for chunk in context_chunks]
    sources = [{'filename': chunk['source_filename'], 'location': chunk['page_or_row']} for chunk in context_chunks]

    prompt = f"Answer the following question based on the provided context:\n\nContext:\n{''.join(context_texts)}\n\nQuestion:\n{query}"
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{'role': 'user', 'content': prompt}]
    )
    answer = response.choices[0].message.content

    return {'answer': answer, 'sources': sources}