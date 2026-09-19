# Vietnamese Traffic Law RAG System 🇻🇳

A Retrieval-Augmented Generation (RAG) system specialized in answering questions about Vietnamese Traffic Law. This system uses a clean, industry-standard FastAPI architecture, integrating Qdrant Vector Database and Large Language Models (supports both **Google Gemini** and **Local Ollama**).

## 🌟 Key Features
- **Standard FastAPI Architecture**: Clean separation of Routers, Schemas, and Dependency Injection.
- **Qdrant Vector DB Integration**: Ultra-fast semantic search for legal texts.
- **Streaming Support**: Emits tokens piece-by-piece (like ChatGPT) for enhanced User Experience (UX).
- **LangSmith Tracing**: Full observability of the AI's Chain of Thought for easy debugging.

---

## 🛠 Installation and Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Variables (.env)
The project requires API Keys to connect to Qdrant and Google Gemini (if using Gemini). 

Create a new file exactly named `.env` in the root directory of the project. Copy the template below into the file and replace the placeholders with your actual API keys:

```env
# ----------------------------------------------------
# 1. REQUIRED: Qdrant Cloud (Vector Database)
# ----------------------------------------------------
# Get your URL and API Key at: https://cloud.qdrant.io/
QDRANT_URL="https://<your_cluster_id>.aws.cloud.qdrant.io"
QDRANT_API_KEY="your_qdrant_api_key_here"

# ----------------------------------------------------
# 2. OPTIONAL: Google Gemini (If using Cloud LLM)
# ----------------------------------------------------
# Get your API Key at: https://aistudio.google.com/
GEMINI_API_KEY="your_gemini_api_key_here"

# ----------------------------------------------------
# 3. OPTIONAL: LangSmith (RAG Tracing)
# ----------------------------------------------------
# Get your credentials at: https://smith.langchain.com/
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY="your_langsmith_api_key_here"
LANGCHAIN_PROJECT="RAG_Legal_VN"
```
> ⚠️ **WARNING:** The `.env` file contains sensitive security keys and must NEVER be uploaded to GitHub. The system is already configured with `.gitignore` to prevent this file from being pushed.

### 3. Choose your LLM Provider (config.yaml)
You can easily switch between Google Gemini and Local Ollama by editing the `config.yaml` file in the root directory:

```yaml
llm_params:
  provider: "gemini" # Change to "ollama" to use local models
  model: "gemini-3.6-flash" # If using ollama, change to your local model name (e.g., "qwen2.5:3b")
```
*Note: If you choose "ollama", make sure you have the Ollama app running on your machine with the specified model pulled.*

### 4. Data Ingestion
If this is your first time running the project, you need to place your legal document files (Word, PDF) into the `data/` directory. After starting the server, call the `/api/ingest` endpoint to chunk the data and push it to Qdrant Cloud.

### 5. Start the Web Server
```bash
python main.py
```
Once the message `Application startup complete` appears, open your browser and navigate to:
👉 **http://localhost:8000/docs**

Here, you will find a beautiful Swagger UI where you can easily test the Chat and Ingest APIs!

---
## 📂 Project Structure
```
RAG_legal/
├── data/                  # Contains raw legal documents (Docx, PDF, etc.)
├── scripts/               # Utility scripts for testing (chunking, retrieval)
├── src/
│   ├── api/               # API Source Code (Routes, Schemas, Dependencies)
│   ├── ingestion/         # Document parsing and chunking logic
│   ├── retrieval/         # RAG pipeline and retrieval logic
│   ├── utils/             # Common utility functions
│   └── vectordb/          # Qdrant connection configuration
├── main.py                # Server entry point
└── requirements.txt       # Python dependencies
```
