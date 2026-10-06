# ============================================================
# ANON AGENT - BUILD RAG INDEX
# ============================================================

import os
import sys

# Add project root to Python path
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(
    0,
    PROJECT_ROOT
)
from database import get_user_activities

from rag.activity_documents import (
    create_activity_documents
)

from rag.vector_store import (
    create_vector_store
)


# ============================================================
# GET ANONYMOUS USER ID
# ============================================================

USER_ID_FILE = "anonymous_user.txt"


def get_user_id():

    if os.path.exists(USER_ID_FILE):

        with open(USER_ID_FILE, "r") as file:
            return file.read().strip()

    return None


# ============================================================
# BUILD RAG INDEX
# ============================================================

def build_rag_index():

    user_id = get_user_id()

    if not user_id:

        print("❌ Anonymous user ID not found.")
        return

    print(
        f"🔐 Building RAG index for: {user_id}"
    )

    activities = get_user_activities(
        user_id
    )

    if not activities:

        print(
            "ℹ️ No activity data found."
        )

        return

    print(
        f"📚 Found {len(activities)} activities."
    )

    documents = create_activity_documents(
        activities
    )

    print(
        f"📄 Created {len(documents)} documents."
    )

    create_vector_store(
        documents
    )

    print(
        "✅ FAISS vector database created successfully."
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    build_rag_index()