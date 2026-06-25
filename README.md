<div align="center">

# HireSense AI

### AI-Powered Resume Ranking, Job Matching & Candidate Fit Intelligence

HireSense AI is a production-ready Flask application that compares a candidate resume against a job description and returns a clear job-fit score, semantic similarity, skill coverage, missing skills, recommended keywords, and resume improvement suggestions.

It combines **Sentence Transformer embeddings**, **FAISS vector search**, **skill-gap analysis**, and **Gemini-powered feedback** with a clean web interface and API-first backend.

<br />

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.3-black)
![Sentence Transformers](https://img.shields.io/badge/Sentence--Transformers-3.0.1-green)
![FAISS](https://img.shields.io/badge/FAISS-Vector%20Search-orange)
![Gemini](https://img.shields.io/badge/Gemini-Optional%20LLM-purple)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![Tests](https://img.shields.io/badge/Pytest-Covered-brightgreen)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Why This Project Matters](#why-this-project-matters)
- [Core Features](#core-features)
- [Demo Workflow](#demo-workflow)
- [System Architecture](#system-architecture)
- [How Matching Works](#how-matching-works)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Build the FAISS Index](#build-the-faiss-index)
- [Run the Application](#run-the-application)
- [Run with Docker](#run-with-docker)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Production Readiness](#production-readiness)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)
- [Future Improvements](#future-improvements)
- [License](#license)

---

## Overview

Recruiters and hiring teams often receive hundreds or thousands of resumes for a single role. Manual screening is slow, inconsistent, and heavily keyword-dependent. HireSense AI helps solve this problem by using natural language understanding and vector similarity to compare resumes with job descriptions more intelligently.

The application accepts a resume as **PDF**, **DOCX**, **TXT**, or pasted text, then compares it with a job description and returns:

- Overall match score from 0 to 100
- Semantic similarity between resume and job description
- Skill coverage percentage
- Matched skills
- Missing skills
- Recommended keywords
- Resume improvement suggestions
- Job fit category
- Similar resumes from the indexed resume corpus

The system is built as a full-stack AI application with a Flask backend, a lightweight frontend, a FAISS vector index, and a modular service-based architecture.

---

## Why This Project Matters

Traditional resume screening tools rely heavily on exact keyword matching. That approach fails when candidates describe the same skill differently from the job description. For example, a resume may say `model deployment`, while a job description may say `ML productionization`. A pure keyword system may miss the relationship.

HireSense AI improves this by combining two signals:

1. **Semantic similarity** using Sentence Transformer embeddings  
2. **Explicit skill coverage** using a curated skills taxonomy

This hybrid approach makes the result more practical than using only embeddings or only keywords.

---

## Core Features

### Resume and Job Matching

Upload or paste a resume and compare it against a job description. The app returns a blended match score based on semantic meaning and skill coverage.

### Semantic Similarity with Sentence Transformers

The project uses `all-MiniLM-L6-v2` by default, a fast and lightweight sentence-transformer model suitable for local CPU execution.

### FAISS-Based Resume Search

HireSense AI can build a FAISS index from a resume corpus and return semantically similar resumes for a given query.

### Skill Gap Analysis

The app extracts skills from both resume and job description, then identifies:

- Skills already present in the resume
- Skills required by the job but missing from the resume
- Keywords that can improve ATS alignment

### Gemini-Powered Suggestions

If a valid Gemini API key is configured, the app generates smart resume improvement suggestions using Gemini. If no key is available, it automatically falls back to rule-based suggestions.

### File Upload Support

Supported resume formats:

- PDF
- DOCX
- TXT

PDF parsing uses `pdfplumber` as the primary parser and `PyPDF2` as a fallback.

### Production-Oriented Backend

The project includes:

- Application factory pattern
- Structured JSON logging
- Request ID tracing
- Security headers
- Rate limiting
- CORS configuration
- Health, readiness, and version endpoints
- Docker support
- Gunicorn production server config
- Pytest test suite

---

## Demo Workflow

```text
Resume File / Resume Text
          |
          v
Text Extraction and Cleaning
          |
          v
Sentence Transformer Embedding
          |
          v
Semantic Similarity Calculation
          |
          v
Skill Gap Analysis
          |
          v
Blended Match Score
          |
          v
Gemini or Rule-Based Suggestions
          |
          v
Final Job Fit Report
```

---

## System Architecture

```text
                       +----------------------+
                       |      Frontend UI      |
                       |  HTML / CSS / JS      |
                       +----------+-----------+
                                  |
                                  v
                       +----------------------+
                       |      Flask API       |
                       |  app factory pattern |
                       +----------+-----------+
                                  |
          +-----------------------+-----------------------+
          |                       |                       |
          v                       v                       v
+-------------------+   +-------------------+   +-------------------+
| Document Parser   |   | Matching Engine   |   | Suggestion Service|
| PDF / DOCX / TXT  |   | Score + Category  |   | Gemini / Fallback |
+---------+---------+   +---------+---------+   +-------------------+
          |                       |
          v                       v
+-------------------+   +-------------------+
| Embedding Service |   | Skill Extractor   |
| Sentence Encoder  |   | Taxonomy Matching |
+---------+---------+   +-------------------+
          |
          v
+-------------------+
| FAISS Index       |
| Similar Resumes   |
+-------------------+
```

---

## How Matching Works

HireSense AI calculates the final match score using a hybrid scoring strategy.

### 1. Semantic Similarity

The resume and job description are converted into dense vector embeddings using a Sentence Transformer model. Their cosine similarity is calculated and rescaled to a human-readable score.

### 2. Skill Coverage

The skill extractor scans the resume and job description against a curated skill taxonomy. It calculates how many job-required skills are present in the resume.

### 3. Blended Score

The final match score combines both signals:

```text
Final Match Score = 60% Semantic Similarity + 40% Skill Coverage
```

This makes the system more balanced:

- Semantic similarity captures meaning and context.
- Skill coverage captures hard requirements and ATS-style alignment.

### 4. Job Fit Category

The final score is mapped to a readable category such as:

- Excellent Fit
- Strong Fit
- Moderate Fit
- Weak Fit
- Poor Fit

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Flask 3.0.3 |
| Production Server | Gunicorn |
| Embeddings | Sentence Transformers |
| Default Model | `all-MiniLM-L6-v2` |
| Vector Search | FAISS CPU |
| LLM Suggestions | Google Gemini API |
| PDF Parsing | pdfplumber, PyPDF2 |
| DOCX Parsing | python-docx |
| Data Processing | Pandas, NumPy |
| ML Utilities | scikit-learn |
| Caching | diskcache |
| Validation | Pydantic |
| Testing | Pytest, pytest-cov |
| Frontend | HTML, CSS, JavaScript |
| Deployment | Docker, Docker Compose |

---

## Project Structure

```text
hiresense-ai/
|
├── app.py
├── wsgi.py
├── gunicorn.conf.py
├── requirements.txt
├── Makefile
├── Dockerfile
├── docker-compose.yml
├── .env.example
|
├── app/
|   ├── __init__.py
|   ├── config.py
|   |
|   ├── api/
|   |   ├── health.py
|   |   └── match.py
|   |
|   ├── core/
|   |   └── exceptions.py
|   |
|   ├── models/
|   |   └── skills_taxonomy.py
|   |
|   ├── services/
|   |   ├── document_parser.py
|   |   ├── embedding_service.py
|   |   ├── faiss_index_service.py
|   |   ├── matching_engine.py
|   |   ├── skill_extractor.py
|   |   └── suggestion_service.py
|   |
|   └── utils/
|       ├── cache.py
|       ├── logging_config.py
|       ├── middleware.py
|       └── validation.py
|
├── data/
|   ├── sample_resumes.csv
|   ├── full_resumes.csv
|   └── faiss_index/
|
├── scripts/
|   └── build_index.py
|
├── static/
|   ├── css/
|   └── js/
|
├── templates/
|   └── index.html
|
└── tests/
    ├── fixtures/
    ├── test_api.py
    ├── test_document_parser.py
    ├── test_embedding_service.py
    ├── test_faiss_index_service.py
    ├── test_matching_engine.py
    ├── test_skill_extractor.py
    └── test_suggestion_service.py
```

---

## Installation

### Prerequisites

Make sure you have the following installed:

- Python 3.10 or higher
- pip
- Git
- Docker, optional
- Gemini API key, optional

### Clone the Repository

```bash
git clone https://github.com/your-username/hiresense-ai.git
cd hiresense-ai
```

### Create Virtual Environment

#### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\activate
```

#### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or using Make:

```bash
make install
```

---

## Environment Variables

Create a `.env` file from the example file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
copy .env.example .env
```

Then update the values as needed.

| Variable | Description | Default / Example |
|---|---|---|
| `FLASK_ENV` | Runtime environment | `production` |
| `FLASK_APP` | Flask entry point | `wsgi.py` |
| `SECRET_KEY` | Flask secret key | Change before deployment |
| `HOST` | App host | `0.0.0.0` |
| `PORT` | App port | `5000` |
| `DEBUG` | Debug mode | `False` |
| `GEMINI_API_KEY` | Gemini API key for AI suggestions | Optional |
| `GEMINI_MODEL` | Gemini model name | `gemini-1.5-flash` |
| `EMBEDDING_MODEL` | Sentence Transformer model | `all-MiniLM-L6-v2` |
| `EMBEDDING_DEVICE` | CPU/GPU device | `cpu` |
| `FAISS_INDEX_PATH` | FAISS index output path | `data/faiss_index/resumes.index` |
| `FAISS_METADATA_PATH` | FAISS metadata path | `data/faiss_index/metadata.json` |
| `RESUME_CORPUS_PATH` | Resume corpus used for indexing | `data/sample_resumes.csv` |
| `MAX_UPLOAD_SIZE_MB` | Max resume upload size | `10` |
| `ALLOWED_EXTENSIONS` | Allowed upload file types | `pdf,docx,txt` |
| `RATE_LIMIT_DEFAULT` | Default API rate limit | `60 per minute` |
| `RATE_LIMIT_MATCH` | Match endpoint rate limit | `10 per minute` |
| `CACHE_DIR` | Embedding cache directory | `.cache` |
| `CACHE_TTL_SECONDS` | Cache expiry | `3600` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Log format | `json` |

> Important: never commit your real `.env` file to GitHub. Keep only `.env.example` in the repository.

---

## Build the FAISS Index

Before using similar-resume search, build the FAISS index.

### Build Index from Sample Corpus

```bash
python scripts/build_index.py
```

Or:

```bash
make build-index
```

This reads:

```text
data/sample_resumes.csv
```

and creates:

```text
data/faiss_index/resumes.index
data/faiss_index/metadata.json
```

### Build Index from Full Corpus

```bash
python scripts/build_index.py --corpus data/full_resumes.csv
```

Use the full corpus when you want better search quality and a more realistic demo.

---

## Run the Application

### Development Mode

```bash
python app.py
```

Or:

```bash
make run
```

Open the app in your browser:

```text
http://localhost:5000
```

### Production-Like Local Run

```bash
gunicorn -c gunicorn.conf.py wsgi:app
```

Or:

```bash
make run-prod
```

---

## Run with Docker

### Build Docker Image

```bash
docker build -t hiresense-ai:latest .
```

Or:

```bash
make docker-build
```

### Run with Docker Compose

```bash
docker compose up --build
```

Or:

```bash
make docker-up
```

The app will be available at:

```text
http://localhost:5000
```

### Stop Containers

```bash
docker compose down
```

Or:

```bash
make docker-down
```

---

## API Documentation

Base URL for local development:

```text
http://localhost:5000/api
```

---

### 1. Health Check

```http
GET /api/health
```

Example:

```bash
curl http://localhost:5000/api/health
```

Response:

```json
{
  "status": "ok"
}
```

---

### 2. Readiness Check

```http
GET /api/ready
```

Example:

```bash
curl http://localhost:5000/api/ready
```

Response:

```json
{
  "status": "ready",
  "checks": {
    "embedding_model_loaded": true,
    "faiss_index_loaded": true
  }
}
```

---

### 3. Version Info

```http
GET /api/version
```

Example:

```bash
curl http://localhost:5000/api/version
```

Response:

```json
{
  "name": "HireSense AI",
  "version": "1.0.0",
  "embedding_model": "all-MiniLM-L6-v2",
  "gemini_enabled": true,
  "faiss_index_size": 120
}
```

---

### 4. Match Resume with Job Description

```http
POST /api/match
```

You can send either:

- `resume_file` with `job_text`
- `resume_text` with `job_text`

#### Multipart Upload Example

```bash
curl -X POST http://localhost:5000/api/match \
  -F "resume_file=@resume.pdf" \
  -F "job_text=We are hiring a Python developer with Flask, SQL, Docker, REST API, and machine learning experience."
```

#### JSON Example

```bash
curl -X POST http://localhost:5000/api/match \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Python developer with Flask, SQL, machine learning, Docker and API development experience...",
    "job_text": "We need a backend engineer skilled in Python, Flask, Docker, SQL and REST APIs..."
  }'
```

#### Example Response

```json
{
  "match_score": 78.4,
  "semantic_similarity": 71.2,
  "skill_coverage_pct": 83.3,
  "job_fit_category": "Strong Fit",
  "matched_skills": [
    "python",
    "flask",
    "docker",
    "sql"
  ],
  "missing_skills": [
    "kubernetes",
    "ci/cd"
  ],
  "recommended_keywords": [
    "kubernetes",
    "ci/cd",
    "microservices"
  ],
  "suggestions": {
    "summary": "Strong alignment with the role, but a few missing deployment and DevOps skills should be highlighted or improved.",
    "improvement_suggestions": [
      "Add measurable backend project impact using numbers.",
      "Mention Docker-based deployment experience clearly.",
      "Include missing keywords if you genuinely have those skills."
    ],
    "rewrite_example": "Python backend developer with experience building Flask APIs, SQL-backed applications, Docker deployments, and machine learning workflows.",
    "source": "gemini"
  },
  "resume_char_count": 2143,
  "job_char_count": 612
}
```

---

### 5. Extract Text from Resume

```http
POST /api/extract-text
```

Useful when you want to preview what the system extracted from a resume file.

Example:

```bash
curl -X POST http://localhost:5000/api/extract-text \
  -F "resume_file=@resume.pdf"
```

Response:

```json
{
  "extracted_text": "Candidate resume text...",
  "char_count": 2450
}
```

---

### 6. Similar Resume Search

```http
POST /api/similar-resumes
```

Example:

```bash
curl -X POST http://localhost:5000/api/similar-resumes \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Data analyst with SQL, Power BI, Python, dashboarding and business reporting experience.",
    "top_k": 5
  }'
```

Response:

```json
{
  "results": [
    {
      "id": "42",
      "category": "Data Science",
      "snippet": "Data analyst experienced in SQL, Python, dashboards...",
      "score": 0.82
    }
  ],
  "count": 5
}
```

---

## Testing

Run the full test suite:

```bash
pytest tests/ -v
```

Or:

```bash
make test
```

Run tests with coverage:

```bash
pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html
```

Or:

```bash
make test-cov
```

The test suite covers:

- API endpoints
- Document parsing
- Embedding service
- FAISS index service
- Matching engine
- Skill extraction
- Suggestion fallback logic

---

## Production Readiness

HireSense AI is designed beyond a basic demo app. It includes several production-focused components.

### Application Factory Pattern

The Flask app is created through `create_app()`, making the project easier to test, configure, and deploy.

### Structured Logging

The app uses structured logging so logs are easier to search and monitor in production systems.

### Request ID Tracing

Each request gets a request ID, making it easier to trace errors and debug user requests end-to-end.

### Rate Limiting

The `/api/match` endpoint is rate-limited separately because it is computationally heavier than normal endpoints.

### Security Headers

The middleware adds common security headers such as:

- `X-Content-Type-Options`
- `X-Frame-Options`
- `Referrer-Policy`
- `Content-Security-Policy`
- `Strict-Transport-Security` outside debug mode

### Health and Readiness Probes

The app exposes health endpoints that are useful for Docker, Kubernetes, and cloud deployments.

### Docker Support

The project includes both `Dockerfile` and `docker-compose.yml` for repeatable deployment.

---

## Troubleshooting

### `ModuleNotFoundError`

Install dependencies again:

```bash
pip install -r requirements.txt
```

Make sure your virtual environment is activated.

### FAISS Index Not Ready

If `/api/similar-resumes` returns an index error, build the index:

```bash
python scripts/build_index.py
```

### Gemini Suggestions Not Working

Check your `.env` file:

```text
GEMINI_API_KEY=your-real-api-key
```

If the key is missing, the app still works using rule-based suggestions.

### App Starts Slowly

The first startup may take time because the Sentence Transformer model is loaded into memory. This is expected.

### Upload Fails

Check:

- File type is PDF, DOCX, or TXT
- File size is below `MAX_UPLOAD_SIZE_MB`
- File is not password-protected or corrupted

### Port Already in Use

Change the port in `.env`:

```text
PORT=8000
```

Then run again:

```bash
python app.py
```

---

## Security Notes

Before pushing to GitHub or deploying publicly:

- Do not commit `.env`
- Rotate any exposed API keys
- Use a strong `SECRET_KEY`
- Restrict `CORS_ALLOWED_ORIGINS`
- Keep `DEBUG=False` in production
- Avoid uploading sensitive real resumes to public demo environments
- Review dataset licensing before redistribution

---

## Future Improvements

Potential improvements for the next version:

- User authentication
- Recruiter dashboard
- Candidate ranking for multiple resumes
- Batch resume upload
- Resume PDF report export
- Admin analytics panel
- Database storage with PostgreSQL
- Background jobs with Celery or RQ
- Cloud deployment on AWS, GCP, Azure, Render, or Railway
- More advanced skill ontology
- ATS-style resume formatting score
- Explainable score breakdown charts
- Role-specific scoring templates

---

## Example Use Cases

HireSense AI can be used for:

- Resume-job matching projects
- HR analytics portfolio projects
- AI-powered recruitment tools
- Applicant tracking system prototypes
- Data science and NLP portfolio demonstrations
- Semantic search learning projects
- Flask production architecture practice

---

## About the Dataset

The project includes sample and full resume corpus files for building the FAISS index. The index is used for semantic resume search and similarity retrieval.

If you publish this project, make sure your dataset usage follows the original dataset license and privacy rules.

---

## License

This project is provided for educational and portfolio purposes. Review third-party dataset and model licenses before commercial use.

---

## Author

**Akshay Rathod**

Data Analyst | Data Science | Machine Learning | AI Applications

---

<div align="center">

### If this project helps you, consider giving it a star on GitHub.

</div>
