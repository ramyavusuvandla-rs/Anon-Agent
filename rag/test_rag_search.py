# ============================================================
# ANON AGENT - RAG SEARCH TEST
# ============================================================

from rag.vector_store import search_similar_activities
from rag.rag_config import TOP_K


# ============================================================
# TEST QUERY
# ============================================================

query = "What activities do I usually practice?"


print("\n🔍 RAG Search Query:")
print(query)


# ============================================================
# SEARCH FAISS
# ============================================================

results = search_similar_activities(
    query,
    top_k=TOP_K
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n📚 Relevant Activities:\n")

for index, document in enumerate(results, start=1):

    print(f"Result {index}")
    print("--------------------")
    print(document.page_content)
    print()