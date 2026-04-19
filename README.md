# DocuMind AI: Secure RAG Workspace 🤖

DocuMind is a production-ready, multi-tenant Retrieval-Augmented Generation (RAG) application. It operates securely within free-tier cloud constraints while delivering enterprise-grade features like OTP Authentication, Vector Namespacing, and Dual-LLM routing for rate-limit protection.

## 🔥 Key Technical Features

### 1. Secure Multi-Tenancy & Hybrid Memory
- **Magic Link OTP Auth**: Built on **Supabase** (PostgreSQL), users authenticate securely via their email without passwords.
- **Isolated Vector Workspaces**: Uses **Pinecone** namespaces dynamically mapped to the user's email, ensuring your documents are hard-siloed from other users.
- **Usage Limits**: Automatically enforces request quotas on a per-user basis in the Supabase cloud backend to prevent abuse.

### 2. High-Availability LLM Routing 
- Operates primary document reasoning through Google's lightweight **Gemini (2.5-flash-lite)**.
- **Fallback Engine**: Implements LangChain fallback routing to intercept 429 Rate Limit exhaustion smoothly. If Gemini hits its quota, the app seamlessly pipelines the prompt to **Groq (Llama-3.3-70B)** with zero user disruption.

### 3. Intelligent Ingestion Pipeline
- **Docling Engine**: Extracts structured data locally from PDFs, XLSX, and TXT files, preserving internal document headers and markdown logic.
- **Deduplication Hashing**: Slices text with massive overlapping windows and hashes chunk signatures to prevent duplicate DB uploads.

---

## 🏗️ Tech Stack & Architectural Decisions

### **Frontend & Application Layer**
*   **Streamlit**: Chosen for its rapid prototyping speed and native Python integration. It acts as the backbone UI while seamlessly handling backend state management via `st.session_state` to ensure secure user authentication flows.

### **Authentication & Database Engine**
*   **Supabase (PostgreSQL)**: Serves as the persistent cloud database. 
    *   *Decision*: Supabase was chosen over local SQLite or heavy cloud providers like AWS Cognito because it offers a generous free tier for OTP (Magic Link) authentication and an incredibly lightweight Python SDK to track usage analytics (enforcing a 5-query soft limit).

### **Vector Storage & Multi-Tenancy**
*   **Pinecone**:
    *   *Decision*: Selected for its serverless architecture and native `namespace` feature. Rather than maintaining massive complex document filters, Pinecone handles multi-tenancy at the architectural level. Every user's embeddings are hard-isolated into a unique namespace based on their email, ensuring zero data leakage between user documents.

### **Inference (LLM) Layer**
*   **LangChain**: The connective tissue linking the vector store to the LLMs.
*   **Google Gemini (2.5-Flash-Lite)**: Serves as the primary, high-speed inference engine.
    *   *Decision*: Selected due to its industry-leading token limits and fast inference on the Google Cloud free tier.
*   **Groq (Llama-3.3-70B-Versatile)**: Serves as the safety net.
    *   *Decision*: Google's generous APIs strictly enforce limits of Requests per Minute (RPM). Rather than crashing during heavy traffic (HTTP 429), the architecture leverages LangChain's `.with_fallbacks()` mechanism to instantly reroute the user's payload to Groq's LPU-accelerated endpoints.

### **Ingestion & Embedding Layer**
*   **Docling**: 
    *   *Decision*: Bypasses traditional PyPDF extractors which break tabular structures. Docling extracts markdown natively, preserving visual relationships in academic papers.
*   **HuggingFace Embeddings (`all-MiniLM-L6-v2`)**: 
    *   *Decision*: Runs locally in memory rather than forcing network requests to OpenAI. Extremely fast and totally free.

---

## 🚀 Local Setup Instructions

**1. Clone & Install**
```bash
git clone https://github.com/your-username/DocuMind.git
cd DocuMind

# Create your virtual environment and install packages
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Configure Environment Secrets**
Create an `.env` file in the root based on `app/.env.example`:
```text
PINECONE_API_KEY="your-pinecone-key"
PINECONE_INDEX_NAME="my-rag-project"

GEMINI_API_KEY="your-google-key"
GROQ_API_KEY="your-groq-key"

SUPABASE_URL="your-supabase-url"
SUPABASE_KEY="your-supabase-secret"

ADMIN_EMAIL="your-admin-email@address.com"
```

**3. Run the App**
```bash
streamlit run main.py
```

---

## ☁️ Cloud Deployment (Streamlit Community Cloud)

1. Connect your GitHub repository to Streamlit Cloud.
2. In the deployment settings dashboard, navigate to **Advanced Settings > Secrets**.
3. Paste all of the key-value pairs from your `.env` file directly into the Streamlit Secrets TOML box. The application's environment bridge automatically pushes them out to LangChain, Supabase, and Pinecone.