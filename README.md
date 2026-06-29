<div align="center">
  <h1>UniQuiz Parser API</h1>
  <p><b>The core backend microservice for the UniQuiz platform, built with FastAPI.</b></p>
  
  [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
  [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
  [![Google Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
</div>

<hr />

## Overview

The **UniQuiz Parser API** is an isolated backend microservice responsible for the heaviest and most complex operations of the UniQuiz ecosystem: parsing unformatted binary documents (DOCX, PDF) and orchestrating interactions with Large Language Models (LLMs) to generate interactive test modules.

By separating this logic from the frontend, we ensure the client remains lightweight and lightning-fast, while this Python microservice handles CPU-intensive text processing and asynchronous network calls to the AI and Database.

---

## The Problems We Solve

### 1. The "Broken Formatting" Dilemma
**Problem:** University professors and students often share testing materials in DOCX or PDF formats that lack standard formatting. They rarely use clean A, B, C, D bullet points. Standard Regular Expressions (RegEx) fail completely when trying to parse monolithic blocks of text.
**Solution (Human Engineering):** We implemented a hybrid approach. The frontend asks the user to input the exact number of answer options present in their file. This API receives that integer and uses it as a strict mathematical validator. The algorithm counts lines and segments, leveraging human input to perfectly slice "broken" text into structured data.

### 2. LLM Hallucinations & JSON Schema Integrity
**Problem:** When asking an AI to generate 30+ questions based on a raw lecture, LLMs often break the JSON structure, hallucinate fields, or forget to mark the correct answer.
**Solution:** This API acts as an AI Orchestrator. We use **Pydantic** models to enforce strict schema validation. The API catches broken AI responses, normalizes them, and ensures the frontend *only* receives a 100% type-safe JSON array.

---

## Architecture & Workflow

1. **Client Request:** The React frontend sends a binary file (or raw text) alongside user parameters (e.g., custom AI instructions, question limits).
2. **Extraction:** The API extracts raw strings using `python-docx` or `PyPDF2`.
3. **Processing Engine:**
   - *If Classic Import:* Text goes through the "Human Engineering" RegEx pipeline.
   - *If AI Generation:* Text is injected into a heavily engineered system prompt and sent to **Google Gemini API**.
4. **Validation:** The resulting data is validated against Pydantic schemas.
5. **Database Sync:** The API uses a Supabase `SERVICE_ROLE_KEY` to safely bypass RLS and inject the generated course directly into the PostgreSQL database.
6. **Response:** A lightweight success status is returned to the client.

---

## Project Structure

```text
uniq-parser-api/
├── app/
│   ├── api/                 # API Routers (endpoints)
│   │   ├── endpoints/       # -> parse.py, ai_generate.py, courses.py
│   │   └── router.py        # Combines all routers
│   ├── core/                # Core configuration (CORS, Settings, Auth)
│   │   └── config.py        # Environment variables loading
│   ├── models/              # Pydantic Schemas for validation
│   │   └── schemas.py       # -> CourseSchema, QuestionSchema, ParsingRequest
│   ├── services/            # Business Logic (The heavy lifting)
│   │   ├── ai_service.py    # Gemini API communication & Prompt Engineering
│   │   ├── doc_parser.py    # Text extraction & Human Engineering algorithms
│   │   └── supabase_db.py   # Secure database transactions
│   └── main.py              # FastAPI application instance & entry point
├── requirements.txt         # Python dependencies
├── .env.example             # Template for environment variables
└── README.md
