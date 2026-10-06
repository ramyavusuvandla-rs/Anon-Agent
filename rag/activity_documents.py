# ============================================================
# ANON AGENT - ACTIVITY DOCUMENTS
# ============================================================

from langchain_core.documents import Document


def create_activity_documents(activities):
    """
    Convert activity history into LangChain documents.

    activities format:
    [
        (activity, timestamp),
        (activity, timestamp),
        ...
    ]
    """

    documents = []

    for activity, timestamp in activities:

        document = Document(
            page_content=(
                f"User activity: {activity}\n"
                f"Timestamp: {timestamp}"
            ),
            metadata={
                "activity": activity,
                "timestamp": str(timestamp),
            }
        )

        documents.append(document)

    return documents