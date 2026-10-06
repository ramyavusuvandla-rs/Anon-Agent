# 🤖 Anon Agent

### Privacy-Preserving Intelligent Routine Monitoring & Assistance Chatbot

Anon Agent is a privacy-preserving AI personal assistant that monitors user activities anonymously, identifies routine patterns, detects changes, and provides intelligent assistance.

The system provides three AI interaction modes:

- Normal Chatbot
- Semi-Agentic AI
- Agentic AI

The application uses an anonymous user ID instead of storing personally identifiable information.

---

## 🚀 Key Features

### 💬 Normal Chatbot
Provides general-purpose conversational assistance using a locally running Qwen3 8B language model through Ollama.

### 🧠 Routine Intelligence
- Records user activities
- Maintains activity history
- Analyzes routine patterns
- Detects recent routine changes
- Compares daily activities
- Provides smart routine suggestions

### 🤖 Semi-Agentic AI
Analyzes detected routine changes and generates appropriate suggestions based on the user's activity pattern.

### ⚙️ Agentic AI
Performs tasks using tools and multi-step decision logic.

Supported tools include:

- Reminder creation
- Calculator
- Calendar
- Weather
- Currency conversion
- Places search
- Bus search and booking demo
- Web search
- Routine analysis
- Activity history
- RAG-based routine memory

### 🔎 RAG-Based Routine Memory

The project uses Retrieval-Augmented Generation (RAG) to retrieve relevant information from previously recorded activities.

Technologies used:

- FAISS
- Hugging Face Embeddings
- LangChain
- Sentence Transformers

### 🔐 Privacy First

- Anonymous user ID
- Local SQLite storage
- Local LLM using Ollama
- API keys stored through environment variables
- Sensitive files excluded using `.gitignore`
- User confirmation before selected actions

---

## 🧠 AI Modes

| Mode | Purpose |
|------|---------|
| Normal Chatbot | General conversational assistance |
| Semi-Agentic AI | Routine analysis and intelligent suggestions |
| Agentic AI | Tool usage, task execution and multi-step actions |

---

## 🛠️ Technologies Used

### Programming Language
- Python 3.10

### AI / ML
- Ollama
- Qwen3 8B
- LangChain
- FAISS
- Hugging Face Embeddings
- Sentence Transformers

### Application
- Streamlit

### Database
- SQLite

### Libraries / Tools
- Pandas
- Scikit-learn
- python-dotenv
- DDGS
- Git
- GitHub

---

## 📂 Project Structure

```text
AnonSense-AI/
│
├── app.py
├── agent_logic.py
├── database.py
├── routine_analysis.py
├── tools.py
├── requirements.txt
├── .gitignore
│
└── rag/
    ├── activity_documents.py
    ├── build_rag_index.py
    ├── rag_config.py
    ├── rag_engine.py
    ├── test_rag_engine.py
    ├── test_rag_search.py
    └── vector_store.py