import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import ollama
from database import (
    create_user_table,
    create_anonymous_user,
    create_activity_table,
    save_activity,
    get_user_activities,
    get_recent_activities,
    get_today_activities,
    get_yesterday_activities,
    create_reminder_table,
    create_bus_booking_table,
    create_calendar_table,
    get_user_reminders,
)

from routine_analysis import (
    analyze_routine,
    detect_routine_change,
    compare_daily_routine,
)

from agent_logic import (
    generate_suggestion,
    run_agent,
    execute_pending_action,
)

from rag.rag_engine import generate_rag_response
from tools import search_routine_memory
# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Anon Agent",
    page_icon="🤖",
    layout="centered",
)

# ============================================================
# CUSTOM UI STYLING
# ============================================================

st.markdown(
    """
    <style>

    /* Main title */
    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    /* Subtitle */
    .main-subtitle {
        text-align: center;
        font-size: 18px;
        opacity: 0.8;
        margin-bottom: 25px;
    }

    /* Feature cards */
    .feature-card {
        padding: 18px;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.25);
        margin-bottom: 10px;
        text-align: center;
    }

    /* Privacy banner */
    .privacy-banner {
        padding: 12px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
        border: 1px solid rgba(128, 128, 128, 0.25);
    }

    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# OPENAI CLIENT
# ============================================================

openai_api_key = os.getenv("OPENAI_API_KEY")

client = (
    OpenAI(api_key=openai_api_key)
    if openai_api_key
    else None
)


# ============================================================
# DATABASE SETUP
# ============================================================

create_user_table()
create_activity_table()
create_reminder_table()
create_bus_booking_table()
create_calendar_table()

# ============================================================
# ANONYMOUS USER
# ============================================================

USER_ID_FILE = "anonymous_user.txt"

if "user_id" not in st.session_state:

    if os.path.exists(USER_ID_FILE):

        with open(USER_ID_FILE, "r") as file:
            st.session_state.user_id = file.read().strip()

    else:

        st.session_state.user_id = create_anonymous_user()

        with open(USER_ID_FILE, "w") as file:
            file.write(st.session_state.user_id)


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_action" not in st.session_state:
    st.session_state.pending_action = None

if "confirmation_message" not in st.session_state:
    st.session_state.confirmation_message = None

if "smart_alert_dismissed" not in st.session_state:
    st.session_state.smart_alert_dismissed = False


# ============================================================
# TITLE / HEADER
# ============================================================

# ============================================================
# PROFESSIONAL HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🤖 Anon Agent</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="main-subtitle">'
    'Privacy-Preserving Intelligent Routine Monitoring & Assistance'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'''
    <div class="privacy-banner">
        🔐 <b>Anonymous User ID:</b> {st.session_state.user_id}
        &nbsp;&nbsp;|&nbsp;&nbsp;
        🛡️ <b>Privacy Mode:</b> Active
    </div>
    ''',
    unsafe_allow_html=True
)

# ============================================================
# FEATURE OVERVIEW
# ============================================================

st.markdown("### 🛠️ Agent Capabilities")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        '<div class="feature-card">'
        '<h3>🤖</h3>'
        '<b>Normal Chatbot</b><br>'
        '<small>AI Conversations</small>'
        '</div>',
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        '<div class="feature-card">'
        '<h3>🧠</h3>'
        '<b>Routine Intelligence</b><br>'
        '<small>RAG & Analysis</small>'
        '</div>',
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        '<div class="feature-card">'
        '<h3>🛠️</h3>'
        '<b>Agent Tools</b><br>'
        '<small>Tasks & Automation</small>'
        '</div>',
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        '<div class="feature-card">'
        '<h3>🔒</h3>'
        '<b>Privacy First</b><br>'
        '<small>Anonymous User</small>'
        '</div>',
        unsafe_allow_html=True
    )


# ============================================================
# NORMAL CHATBOT
# ============================================================

st.subheader("💬 Normal Chatbot")


# -----------------------------
# Display Previous Messages
# -----------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.write(message["content"])


# -----------------------------
# Chat Input
# -----------------------------

user_message = st.chat_input(
    "Type your message here..."
)


# -----------------------------
# Process User Message
# -----------------------------

if user_message:

    with st.chat_message("user"):
        st.write(user_message)

    # Save user message in session history
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    # Save user activity in SQLite
    save_activity(
        st.session_state.user_id,
        user_message,
    )

    # Send message to OpenAI
        # ============================================================
    # SEND MESSAGE TO OLLAMA
    # ============================================================

    try:

        response = ollama.chat(
            model="qwen3:8b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Anon Agent, a friendly and helpful "
                        "privacy-preserving personal assistant. "
                        "Give clear, simple and useful answers."
                    )
                }
            ] + st.session_state.messages
        )

        assistant_response = response["message"]["content"]

    except Exception as error:

        st.error(
            f"⚠️ An error occurred while contacting Ollama: {error}"
        )

        st.stop()

    # ============================================================
    # DISPLAY AI RESPONSE
    # ============================================================

    with st.chat_message("assistant"):

        st.write(
            assistant_response
        )

    # ============================================================
    # SAVE AI RESPONSE
    # ============================================================

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": assistant_response,
        }
    )

    assistant_response = response["message"]["content"]

    # Display AI response
    with st.chat_message("assistant"):
        st.write(assistant_response)

    # Save AI response in session history
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": assistant_response,
        }
    )


# ============================================================
# ROUTINE DATA COLLECTION
# ============================================================

recent_activities = get_recent_activities(
    st.session_state.user_id,
    limit=10,
)

today_activities = get_today_activities(
    st.session_state.user_id
)

yesterday_activities = get_yesterday_activities(
    st.session_state.user_id
)


daily_comparison = compare_daily_routine(
    today_activities,
    yesterday_activities,
)

routine_result = analyze_routine(
    recent_activities
)

change_result = detect_routine_change(
    recent_activities
)

suggestion_result = generate_suggestion(
    change_result
)


# ============================================================
# DAILY ROUTINE COMPARISON
# ============================================================

st.subheader("📅 Daily Routine Comparison")

if daily_comparison["status"] == "routine_deviation":

    st.warning(
        f"⚠️ {daily_comparison['message']}"
    )

    if daily_comparison.get("missing_today"):
        st.write(
            "🔴 Missing today:",
            ", ".join(daily_comparison["missing_today"]),
        )

    if daily_comparison.get("new_today"):
        st.write(
            "🟢 New today:",
            ", ".join(daily_comparison["new_today"]),
        )

elif daily_comparison["status"] == "no_deviation":

    st.success(
        f"✅ {daily_comparison['message']}"
    )

elif daily_comparison["status"] == "not_enough_comparison_data":

    st.info(
        f"ℹ️ {daily_comparison['message']}"
    )

else:

    st.info(
        f"ℹ️ {daily_comparison['message']}"
    )


# ============================================================
# SMART ROUTINE ALERT
# ============================================================

if (
    daily_comparison["status"] == "routine_deviation"
    and not st.session_state.smart_alert_dismissed
):

    missing_today = daily_comparison.get(
        "missing_today",
        [],
    )

    if missing_today:

        st.warning(
            "🔔 Smart Routine Alert\n\n"
            f"You usually do: {', '.join(missing_today)} "
            "but it has not been recorded today."
        )

        st.info(
            "💡 Anon Agent noticed a change in your "
            "usual routine and is alerting you."
        )

        alert_col1, alert_col2 = st.columns(2)

        # --------------------------------------------------------
        # REMIND ME
        # --------------------------------------------------------

        with alert_col1:

            if st.button(
                "⏰ Remind me",
                key="routine_alert_remind",
            ):

                activity = missing_today[0]

                st.session_state.pending_action = {
                    "action": "create_reminder",
                    "task": f"Do {activity}",
                    "minutes": 60,
                }

                st.session_state.confirmation_message = (
                    f"⏰ Would you like me to remind you to "
                    f"**do {activity}** in 60 minutes?"
                )

                st.session_state.smart_alert_dismissed = True

                st.rerun()

        # --------------------------------------------------------
        # DISMISS
        # --------------------------------------------------------

        with alert_col2:

            if st.button(
                "❌ Dismiss",
                key="routine_alert_dismiss",
            ):

                st.session_state.smart_alert_dismissed = True

                st.success(
                    "✅ Smart Routine Alert dismissed."
                )


# ============================================================
# ROUTINE INSIGHTS
# ============================================================

if routine_result["status"] == "success":

    st.info(
        f"🧠 Most common activity: "
        f"{routine_result['most_common_activity']}"
    )

# ============================================================
# RAG ROUTINE MEMORY SEARCH
# ============================================================

st.subheader("🧠 RAG Routine Memory")

rag_query = st.text_input(
    "Ask about your previous routine or activities:",
    placeholder="Example: What do I usually practice?"
)

if st.button("🔍 Search My Routine Memory"):

    if rag_query:

        with st.spinner("Searching your routine memory..."):

            rag_result = search_routine_memory(
                rag_query
            )

        st.success("✅ Relevant routine memory found:")

        st.write(rag_result)

    else:

        st.warning(
            "Please enter a question about your routine."
        )
        
        
# -----------------------------
# Routine Change Detection
# -----------------------------

if change_result["status"] == "change_detected":

    st.warning(
        f"⚠️ Routine change detected: "
        f"{change_result['message']}"
    )


# -----------------------------
# Semi-Agentic Suggestion
# -----------------------------

if suggestion_result["status"] == "suggestion":

    st.info(
        f"💡 Anon Agent Suggestion: "
        f"{suggestion_result['message']}"
    )


# -----------------------------
# No Change / Not Enough Data
# -----------------------------

if change_result["status"] == "no_change":

    st.success(
        "✅ No significant routine change detected."
    )

elif change_result["status"] == "not_enough_data":

    st.info(
        "ℹ️ Not enough activity data to detect "
        "routine changes yet."
    )


# -----------------------------
# Recent Activities Count
# -----------------------------

if recent_activities:

    st.info(
        f"Anon Agent found "
        f"{len(recent_activities)} recent activities."
    )


# ============================================================
# ACTIVITY HISTORY
# ============================================================

st.subheader("📋 Activity History")

activities = get_user_activities(
    st.session_state.user_id
)

if activities:

    for activity, timestamp in activities:

        st.write(
            f"📝 {activity} — 🕒 {timestamp}"
        )

else:

    st.info(
        "No activities recorded yet."
    )
    
# ============================================================
# AGENT MODES
# ============================================================

st.markdown("### 🧩 Agent Modes")

mode1, mode2, mode3 = st.columns(3)

with mode1:
    st.markdown(
        '<div class="feature-card">'
        '<h3>💬 Normal Chatbot</h3>'
        '<small>Answers user questions using the local AI model.</small>'
        '</div>',
        unsafe_allow_html=True
    )

with mode2:
    st.markdown(
        '<div class="feature-card">'
        '<h3>🧠 Semi-Agentic AI</h3>'
        '<small>Analyzes routines and provides intelligent suggestions.</small>'
        '</div>',
        unsafe_allow_html=True
    )

with mode3:
    st.markdown(
        '<div class="feature-card">'
        '<h3>🤖 Agentic AI</h3>'
        '<small>Uses tools to perform tasks with user confirmation.</small>'
        '</div>',
        unsafe_allow_html=True
    )
    
# ============================================================
# PRIVACY INFORMATION
# ============================================================

st.markdown("### 🔐 Privacy & Security")

privacy1, privacy2, privacy3 = st.columns(3)

with privacy1:
    st.markdown(
        '<div class="feature-card">'
        '<h3>🆔</h3>'
        '<b>Anonymous Identity</b><br>'
        '<small>No personal name required.</small>'
        '</div>',
        unsafe_allow_html=True
    )

with privacy2:
    st.markdown(
        '<div class="feature-card">'
        '<h3>💾</h3>'
        '<b>Local Storage</b><br>'
        '<small>Routine data is stored locally.</small>'
        '</div>',
        unsafe_allow_html=True
    )

with privacy3:
    st.markdown(
        '<div class="feature-card">'
        '<h3>🛡️</h3>'
        '<b>User Confirmation</b><br>'
        '<small>Actions require confirmation.</small>'
        '</div>',
        unsafe_allow_html=True
    )



# ============================================================
# AGENTIC AI
# ============================================================

st.subheader("🤖 Agentic AI")

agent_message = st.text_input(
    "What would you like Anon Agent to do?"
)


# -----------------------------
# Ask Agent
# -----------------------------

if st.button("🤖 Ask Anon Agent"):

    if agent_message:

        agent_result = run_agent(
            st.session_state.user_id,
            agent_message,
        )

        if agent_result["status"] == "confirmation_required":

            st.session_state.pending_action = (
                agent_result["pending_action"]
            )

            st.session_state.confirmation_message = (
                agent_result["message"]
            )

        elif agent_result["status"] == "agent_action_completed":

            st.success(
                f"✅ {agent_result['message']}"
            )

        else:

            st.info(
                agent_result["message"]
            )

    else:

        st.warning(
            "Please enter a request."
        )


# ============================================================
# CONFIRMATION SECTION
# ============================================================

if (
    st.session_state.pending_action
    and st.session_state.confirmation_message
):

    st.warning(
        st.session_state.confirmation_message
    )

    col1, col2 = st.columns(2)

    # -----------------------------
    # YES BUTTON
    # -----------------------------

    with col1:

        if st.button(
            "✅ Yes, proceed",
            key="confirm_action",
        ):

            result = execute_pending_action(
                st.session_state.user_id,
                st.session_state.pending_action,
            )

            if result["status"] == "agent_action_completed":

                st.success(
                    f"✅ {result['message']}"
                )

            else:

                st.error(
                    result["message"]
                )

            # Clear pending action
            st.session_state.pending_action = None
            st.session_state.confirmation_message = None

    # -----------------------------
    # NO BUTTON
    # -----------------------------

    with col2:

        if st.button(
            "❌ No, cancel",
            key="cancel_action",
        ):

            st.info(
                "❌ Action cancelled."
            )

            st.session_state.pending_action = None
            st.session_state.confirmation_message = None


# ============================================================
# REMINDER HISTORY
# ============================================================

st.subheader("⏰ Reminder History")

reminders = get_user_reminders(
    st.session_state.user_id
)

if reminders:

    for task, reminder_time, created_at in reminders:

        st.write(
            f"🔔 {task} — 🕒 {reminder_time}"
        )

else:

    st.info(
        "No reminders created yet."
    )
