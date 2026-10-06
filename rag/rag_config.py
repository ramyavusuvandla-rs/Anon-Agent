# ============================================================
# ANON AGENT - RAG CONFIGURATION
# ============================================================

# Embedding model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# FAISS vector database location
VECTOR_DB_PATH = "rag/faiss_index"

# Number of relevant documents to retrieve
TOP_K = 3