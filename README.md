### Overview

This project is a production-ready Retrieval-Augmented Generation (RAG) application designed to operate entirely within free-tier cloud constraints without sacrificing enterprise-grade features.

Rather than relying on expensive API calls for every step of the pipeline, this architecture utilizes a Hybrid-Compute Model: it processes documents and generates vector embeddings locally using open-source models, while offloading the LLM reasoning to Google's lightweight Gemini API. It is designed with secure multi-tenancy, rate limiting, and intelligent document parsing to simulate a true SaaS environment.

### Key Features

- **Hybrid-Compute Architecture**: Minimizes API costs by performing heavy lifting (OCR, embedding generation) locally.
- **Intelligent Document Parsing**: Uses Docling to extract text from PDFs, images, and spreadsheets, preserving document structure.
- **Secure Multi-Tenancy**: Implements strict data isolation using Pinecone namespaces to ensure user data privacy.
- **Rate Limiting**: Built-in request throttling to prevent abuse and manage API costs.
- **Scalable Vector Storage**: Utilizes Pinecone for efficient vector storage and retrieval.
- **Real-time Feedback**: Provides instant feedback on document processing status and query results.