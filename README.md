# CaseCanopy

## Overview
CaseCanopy is an AI-powered legal platform that bridges the justice gap by enabling cross-jurisdiction legal precedent discovery and outcome prediction. It provides equal access to legal insights through a modern, responsive web application.

## Project Structure
- **agentic-ai/**: Python FastAPI service for legal document generation using AI.
- **backend/**: Go (Gin) backend for user, admin, file, and document management.
- **frontend/**: Next.js/React frontend for user interaction and legal research.
- **RAG/**: Python Flask server for retrieval-augmented generation (LangChain-based).

## Key Features
- **AI-powered legal document generation** (petitions, RTIs, complaints, etc.)
- **Case law and legal precedent search**
- **Outcome prediction and legal insights**
- **User authentication and admin approval**
- **Document upload, management, and PDF generation**
- **Modern, responsive frontend UI**

## Services Overview

### 1. agentic-ai (Python/FastAPI)
- Generates legal documents (PDFs) from user input or backend data.
- Uses OpenAI and LangChain for document creation.
- Endpoints:
  - `/generate_document` (POST): Generate a document from user input.
  - `/generate_from_backend` (GET): Generate a document from backend API data.
- Dependencies: FastAPI, LangChain, OpenAI, ReportLab, Jinja2, etc.

### 2. backend (Go/Gin)
- Handles user management, file uploads, admin approval, and document parsing.
- Connects to MongoDB.
- Key routes:
  - `/api/upload`, `/api/transcribe`, `/api/signup-legal`, `/api/signin`
  - `/api/users`, `/api/users/:id`
  - `/api/admin/login`, `/api/admin/users/legal`, `/api/admin/users/legal/approve`
  - `/api/submit` (searches)
- Modular structure: controllers, services, middleware, models.

### 3. frontend (Next.js/React)
- User authentication, dashboard, search, upload, and results pages.
- Features animated landing page, guided tour, and modern UI.
- Uses Tailwind CSS, Framer Motion, and other modern libraries.

### 4. RAG (Python/Flask)
- LangChain-based retrieval-augmented generation for legal queries.
- Endpoints:
  - `/api/plain-text` (GET): Query the LangChain model.
  - `/api/saved-query` (GET): Retrieve the last saved query.
- Dependencies: Flask, LangChain, OpenAI, Qdrant, etc.

## Setup Instructions

### agentic-ai
```bash
cd agentic-ai
python3.10 -m venv legal_venv
source legal_venv/bin/activate
pip install -r requirements.txt
# Add your OpenAI API key to .env
uvicorn main:app --reload --port 8001
```

### backend
```bash
cd backend
go mod tidy
go run main.go
# Server runs on :8000, requires MongoDB running locally
```

### frontend
```bash
cd frontend
npm install
npm run dev
# App runs on http://localhost:3000
```

### RAG
```bash
cd RAG
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Add your OpenAI API key to .env
python app.py
# Server runs on http://localhost:8000
```

## Environment Variables
- **agentic-ai/.env** and **RAG/.env** require:
  ```
  OPENAI_API_KEY=your_openai_api_key_here
  ```
- **backend** expects MongoDB at `mongodb://localhost:27017`.

## Example API Usage
- **Generate Legal Document (agentic-ai):**
  ```
  POST /generate_document
  {
    "user_input": "Describe your legal issue...",
    "user_name": "John Doe",
    "location": "City, State",
    "contact_number": "1234567890",
    "language": "en"
  }
  ```
- **Search Case Law (frontend/backend):**
  - Use the frontend search interface, which interacts with backend and RAG services.

## Contribution
- Fork the repo, create a feature branch, and submit a pull request.
- Ensure code is well-documented and tested.

## License
- See `frontend/LICENSE` for details.