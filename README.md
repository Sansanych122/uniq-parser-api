<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=005571&height=250&section=header&text=UniQuiz%20Parser%20API&fontSize=60&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=The%20core%20backend%20microservice%20built%20with%20FastAPI&descAlignY=55&descSize=20" width="100%" alt="Header Banner" />
  
  <br /><br />
  
  [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
  [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
  [![Google Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
</div>

<hr />

# UniQuiz Parser API

A FastAPI-based microservice dedicated to doing the heavy lifting for the UniQuiz platform. It extracts text from unstructured academic documents and orchestrates LLM generation, ensuring the frontend doesn't crash from malformed data.

## The Problem

Educational materials are a formatting nightmare. University lectures and test banks in PDF or DOCX formats rarely follow clean formatting rules. Standard parsers fail when bullet points are missing. Furthermore, relying purely on LLMs to generate 30+ structured questions directly from raw text often results in JSON hallucinations, missing fields, or incorrect schema types.

## The Solution

This API acts as an aggressive filter and orchestrator:
*   **Human Engineering Parsing:** For classic test imports, the frontend passes a user-defined integer (the exact number of answer options). The backend uses this number as a mathematical validator to slice through broken, unformatted text with surgical precision.
*   **LLM Orchestration:** Integrates the Google Gemini API to read raw text and generate tests based on custom user prompts. 
*   **Strict Schema Enforcement:** Catches the AI's output and forces it through strict validation schemas. If the AI hallucinates, the backend handles it, guaranteeing the frontend only receives 100% type-safe data.

## Tech Stack

*   **FastAPI (Python):** Handles high-performance, asynchronous routing and I/O operations.
*   **Pydantic:** Enforces strict data validation and serialization.
*   **Google Gemini API:** Generates contextual questions from raw text.
*   **Supabase (PostgreSQL):** Facilitates secure, direct database writes bypassing frontend limitations.

## Project Structure

The architecture is modular, separating routing from business logic and data models:

```text
├── core/
│   └── config.py              # Environment configuration and secrets
├── models/
│   └── schemas.py             # Pydantic schemas for strict data validation
├── routers/
│   ├── parse.py               # Endpoints for file parsing algorithms
│   └── save.py                # Endpoints for secure database injection
├── services/
│   ├── parsers/
│   │   ├── docx_parser.py     # DOCX binary extraction
│   │   ├── pdf_parser.py      # PDF binary extraction
│   │   └── txt_parser.py      # Plain text handling
│   ├── file_router.py         # Routes incoming files to the appropriate parser
│   ├── gemini_service.py      # Google Gemini API integration and prompt logic
│   └── supabase_writer.py     # Secure database transaction handling
├── .gitignore
├── main.py                    # FastAPI application entry point
└── requirements.txt           # Project dependencies
