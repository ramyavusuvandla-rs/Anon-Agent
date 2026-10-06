# ============================================================
# ANON AGENT - FAISS VECTOR STORE
# ============================================================

import os

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from rag.rag_config import (
    EMBEDDING_MODEL,
    VECTOR_DB_PATH,
)


# ============================================================
# CREATE EMBEDDING MODEL
# ============================================================

def create_embedding_model():

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )

    return embeddings


# ============================================================
# CREATE FAISS VECTOR STORE
# ============================================================

def create_vector_store(documents):

    embeddings = create_embedding_model()

    vector_store = FAISS.from_documents(
        documents,
        embeddings
    )

    os.makedirs(
        VECTOR_DB_PATH,
        exist_ok=True
    )

    vector_store.save_local(
        VECTOR_DB_PATH
    )

    return vector_store


# ============================================================
# LOAD FAISS VECTOR STORE
# ============================================================

def load_vector_store():

    embeddings = create_embedding_model()

    vector_store = FAISS.load_local(
        VECTOR_DB_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vector_store


# ============================================================
# SEARCH RELEVANT ACTIVITIES
# ============================================================

def search_similar_activities(
    query,
    top_k=3
):

    vector_store = load_vector_store()

    results = vector_store.similarity_search(
        query,
        k=top_k
    )

    return results