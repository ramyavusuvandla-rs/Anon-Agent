# ============================================================
# ANON AGENT - RAG ENGINE
# ============================================================

import os

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIError

from rag.vector_store import search_similar_activities
from rag.rag_config import TOP_K


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

client = (
    OpenAI(api_key=api_key)
    if api_key
    else None
)


# ============================================================
# RETRIEVE RELEVANT ACTIVITIES
# ============================================================

def retrieve_relevant_activities(
    query,
    top_k=TOP_K
):

    results = search_similar_activities(
        query,
        top_k=top_k
    )

    return results


# ============================================================
# GENERATE RAG RESPONSE
# ============================================================

def generate_rag_response(query):

    # --------------------------------------------------------
    # Retrieve relevant activity history
    # --------------------------------------------------------

    documents = retrieve_relevant_activities(
        query
    )

    if not documents:

        return (
            "I could not find relevant activity "
            "history for your question."
        )

    # --------------------------------------------------------
    # Build retrieved context
    # --------------------------------------------------------

    context = "\n\n".join(
        document.page_content
        for document in documents
    )

    # --------------------------------------------------------
    # Check API key
    # --------------------------------------------------------

    if client is None:

        return (
            "🧠 Relevant Routine Memory:\n\n"
            f"{context}\n\n"
            "ℹ️ OpenAI API key is not configured, "
            "so the retrieved activities are shown "
            "directly."
        )

    # --------------------------------------------------------
    # Prompt
    # --------------------------------------------------------

    prompt = f"""
You are Anon Agent, a privacy-preserving
personal routine assistant.

Answer the user's question using ONLY the
retrieved activity history provided below.

Retrieved activity history:
---------------------------
{context}
---------------------------

User question:
{query}

Instructions:
- Give a clear and natural answer.
- Base the answer only on the retrieved history.
- Do not invent activities or facts.
- If the history is insufficient, say that clearly.
- Keep the response concise.
"""

    # --------------------------------------------------------
    # OpenAI request
    # --------------------------------------------------------

    try:

        response = client.chat.completions.create(
            model="gpt-5.6-luna",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You answer questions using "
                        "retrieved personal routine context."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content

    # --------------------------------------------------------
    # API quota / rate limit
    # --------------------------------------------------------

    except RateLimitError:

        return (
            "🧠 Relevant Routine Memory:\n\n"
            f"{context}\n\n"
            "⚠️ OpenAI API credits are exhausted, "
            "so the AI-generated summary is currently "
            "unavailable.\n\n"
            "✅ However, the RAG system successfully "
            "retrieved the relevant routine history."
        )

    # --------------------------------------------------------
    # Other OpenAI API errors
    # --------------------------------------------------------

    except APIError as error:

        return (
            "🧠 Relevant Routine Memory:\n\n"
            f"{context}\n\n"
            "⚠️ The AI response could not be generated "
            f"because of an OpenAI API error: {error}\n\n"
            "✅ The RAG retrieval itself was successful."
        )

    # --------------------------------------------------------
    # Unexpected errors
    # --------------------------------------------------------

    except Exception as error:

        return (
            "🧠 Relevant Routine Memory:\n\n"
            f"{context}\n\n"
            "⚠️ An unexpected error occurred while "
            f"generating the AI response: {error}\n\n"
            "✅ The retrieved routine history is shown above."
        )