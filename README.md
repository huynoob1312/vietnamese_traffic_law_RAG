# Vietnamese Traffic Law RAG System 🇻🇳 ⚖️

An advanced, full-stack **Retrieval-Augmented Generation (RAG)** pipeline designed specifically for querying and reasoning over Vietnamese Traffic Laws. This system leverages state-of-the-art Information Retrieval techniques to provide highly accurate legal consultation through a modern web interface.

## 🌟 Key Features

*   **Hybrid Retrieval Architecture**: Fuses sparse term-matching (BM25) with dense semantic embeddings (`multilingual-e5-small`, `bge-m3`) using **Reciprocal Rank Fusion (RRF)** to handle both exact keyword matches and broad semantic queries.
*   **Two-Stage Ranking (Cross-Encoder)**: Integrates `BAAI/bge-reranker-v2-m3` as a second-stage reranker, significantly boosting Retrieval Accuracy (Recall@10) on complex legal datasets.
*   **Domain-Specific Semantic Chunking**: Parsers designed explicitly for Vietnamese legal document hierarchies (Article/Clause/Point - *Điều/Khoản/Điểm*), preserving context integrity for LLMs and minimizing hallucination.
*   **Extensive Benchmarking Framework**: Includes automated evaluation scripts capable of measuring MAP, MRR, and Recall metrics against 1,500+ query-context pairs, featuring API rate-limit resilience.
*   **Modern Full-Stack Integration**: 
    *   **Backend**: Scalable FastAPI architecture with hot-reloadable configurations and MySQL database for chat history persistence.
    *   **Frontend**: Responsive UI built with React.js, Vite, and Tailwind CSS, featuring an Admin Dashboard to monitor system stats and manage vector ingestion.

---

## 🛠 Tech Stack

*   **AI/ML & NLP**: LangChain, HuggingFace Transformers, Sentence-Transformers
*   **Vector Database**: Qdrant Cloud
*   **Relational Database**: MySQL (SQLAlchemy ORM)
*   **LLM Providers**: Google Gemini API, Local Ollama (`qwen2.5`)
*   **Backend**: Python, FastAPI, Uvicorn
*   **Frontend**: React.js, Vite, Tailwind CSS

---

## 🚀 Installation and Setup

### 1. Prerequisites
*   **Python 3.10+**
*   **Node.js 18+** (Required for the React frontend)
*   **MySQL Server** (Running locally or remotely)
*   **Qdrant Cloud Account** (For Vector DB)

### 2. Clone the Repository
```bash
git clone https://github.com/your-username/vietnamese_traffic_law_RAG.git
cd vietnamese_traffic_law_RAG
```

### 3. Backend Setup (FastAPI)
```bash
# Install Python dependencies
pip install -r requirements.txt
```

Create a `.env` file in the root directory:
```env
# Vector Database
QDRANT_URL="https://<your_cluster_id>.aws.cloud.qdrant.io"
QDRANT_API_KEY="your_qdrant_api_key_here"

# LLM Providers (Add based on your config.yaml preference)
GEMINI_API_KEY="your_gemini_api_key_here"

# Observability (Optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY="your_langsmith_api_key_here"
LANGCHAIN_PROJECT="RAG_Legal_VN"
```

### 4. Frontend Setup (React/Vite)
```bash
cd frontend
npm install
```

---

## 💻 Running the Application

You need to run both the Backend and Frontend servers concurrently.

**Terminal 1: Start the Backend Server**
```bash
# From the root directory
python main.py
```
*The backend API will run on http://localhost:8000.*

**Terminal 2: Start the Frontend Server**
```bash
# From the frontend directory
cd frontend
npm run dev
```
*The frontend UI will run on http://localhost:5173 (or the port specified by Vite). Open this link in your browser to interact with the AI.*

---

## ⚙️ Configuration & Data Ingestion

### Dynamic Configuration (`config.yaml`)
You can control the entire behavior of the RAG pipeline via the Admin UI or by editing `config.yaml`. The system supports hot-reloading for most parameters:
*   **Embedding Models**: Switch between `e5-small`, `bge-m3`, etc.
*   **LLM Provider**: Toggle between `gemini` and `ollama`.
*   **Retrieval**: Configure `search_type` (hybrid/vector/bm25), `top_k`, and turn the reranker on/off.

### Ingesting Legal Documents
1. Place your raw legal files (`.docx`, `.pdf`) inside the `data/` directory.
2. Open the Web UI, navigate to the **Admin Dashboard**, and trigger the **Re-index / Ingest** process. The system will chunk the documents and push the vectors to Qdrant automatically in the background.

---

The system was evaluated on a custom benchmark dataset containing 1,500+ complex legal queries. Below is a comparison of different retrieval strategies and embedding models, measuring accuracy and latency:

![Benchmark Results](assets/benchmark_results.png)

*(Note: The metrics above were measured on Google Colab using a T4 GPU / CPU infrastructure. The Hybrid + Reranker pipeline yields the highest accuracy but requires more compute time).*

To reproduce these results or run the evaluation pipeline on a new dataset:
```bash
python benchmark/run_benchmark.py
```

---

## 📂 Project Structure
```text
RAG_legal/
├── benchmark/             # Evaluation scripts, datasets, and checkpointing
├── data/                  # Contains raw legal documents (.docx, .pdf)
├── frontend/              # React/Vite web application source code
├── src/
│   ├── api/               # FastAPI Routes, Schemas, Dependencies
│   ├── db/                # MySQL Models and Database configurations
│   ├── ingestion/         # Legal document chunking and parsing logic
│   ├── llm/               # LLM integrations (Gemini, Ollama)
│   ├── retrieval/         # Hybrid RAG pipeline and reranking logic
│   ├── utils/             # Common utility functions & configurations
│   └── vectordb/          # Qdrant connection and vector operations
├── config.yaml            # Dynamic runtime configuration for the system
├── main.py                # FastAPI server entry point
└── requirements.txt       # Python backend dependencies
```

---
*Developed as an advanced Information Retrieval & AI reasoning project.*
