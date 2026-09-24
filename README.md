```markdown
# Secure Parcel Routing Engine 📦

A production-grade, rule-based logistics routing engine built with **FastAPI**, **Pydantic V2**, and **Tailwind CSS**. This system ingests parcel data, sanitizes it, evaluates it against a configurable YAML ruleset, and deterministically routes the package to the correct department.

## 🚀 Features & Architecture

This project was built with a strict focus on **Security**, **Observability**, and **Maintainability**.

### 1. Core Engine (`app/routing/`)
- **Dynamic Rules Loading:** Routing logic is decoupled from code. Rules are defined in `config/rules.yaml` and loaded into memory on server startup.
- **Strict Validation:** Uses Pydantic V2 to enforce schema constraints (e.g., preventing negative weights or unsupported country codes).
- **Safe Evaluation:** Uses sandboxed Python `eval()` with restricted globals to process mathematical and logical routing conditions dynamically.

### 2. Security First (`app/core/security.py`)
- **API Key Authentication:** All endpoints are protected via an `X-API-Key` header.
- **Rate Limiting:** IP-based tracking to prevent DDoS attacks or abuse.
- **Payload Sanitization:** Custom parsing logic intercepts raw JSON to strip null bytes, prevent deeply nested structures (Billion Laughs attack), and neutralize basic XSS vectors before Pydantic ever sees the data.
- **Middleware Protections:** Strict payload size limits and OWASP-recommended security headers.

### 3. Production Observability (`app/core/logging.py` & `errors.py`)
- **Structured JSON Logging:** All logs are output in JSON format, ready for ingestion by tools like Datadog, ELK, or CloudWatch.
- **PII Masking:** Email addresses and card numbers are automatically redacted using regex at the logging layer.
- **Request Tracing:** A unique `X-Request-ID` is generated for every call, injected into the logging context, and returned to the client.
- **Safe Exception Handling:** A global error handler catches unhandled exceptions, logs the full stack trace internally, but returns a sterile HTTP 500 response to the client to prevent information leakage.

### 4. Interactive Dashboard (`app/static/index.html`)
- A clean, responsive UI built with Tailwind CSS served directly via FastAPI.
- Allows real-time testing of the routing rules and visualizes system crashes securely.

## 🛠️ Tech Stack
- **Backend:** Python 3.11, FastAPI, Uvicorn, Pydantic V2
- **Testing:** Pytest, AnyIO
- **Frontend:** HTML5, JavaScript, Tailwind CSS (via CDN)
- **CI/CD:** GitHub Actions

## 🚦 Getting Started

### Installation
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt

```

### Running the Server

```bash
uvicorn app.main:app --reload

```

Navigate to `http://127.0.0.1:8000` to access the Dashboard.

### Running Tests

```bash
pytest

```

```

```