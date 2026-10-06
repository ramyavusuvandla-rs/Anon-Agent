# ============================================================
# ANON AGENT - RAG ENGINE TEST
# ============================================================

from rag.rag_engine import generate_rag_response


# ============================================================
# TEST QUERY
# ============================================================

query = "What do I usually practice?"


print("\n🤖 Anon Agent RAG Test")
print("======================")

print(f"\n👤 User Question:")
print(query)


# ============================================================
# GENERATE RESPONSE
# ============================================================

response = generate_rag_response(
    query
)


# ============================================================
# DISPLAY RESPONSE
# ============================================================

print("\n🧠 Anon Agent Response:")
print("-----------------------")
print(response)
print()