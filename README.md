# Secure Parcel Routing Engine 📦

A production-grade, rule-based logistics routing engine built with **FastAPI**, **Pydantic V2**, and **Tailwind CSS**. This system ingests parcel data, sanitizes it, evaluates it against a configurable YAML ruleset, and deterministically routes the package to the correct department.

---

## 🖥️ System Interface

![Dashboard Screenshot](image_59f51a.png)
*The interactive operator dashboard supporting both single-parcel evaluation and JSON batch uploads with partial-failure handling.*

---

## 🚀 Features & Architecture

This project was built with a strict focus on **Security**, **Observability**, and **Maintainability**.

### 1. Core Engine (`app/routing/`)
- **Dynamic Rules Loading:** Routing logic is decoupled from code. Rules are defined in `config/rules.yaml` and loaded into memory on server startup.
- **Strict Validation:** Uses Pydantic V2 to enforce schema constraints (e.g., preventing negative weights or unsupported country codes).
- **Safe Evaluation:** Uses sandboxed Python `eval()` with restricted globals to process mathematical and logical routing conditions dynamically.
- **Batch Processing:** Dedicated endpoint for bulk JSON ingestion, designed to process valid parcels even if adjacent array items contain bad data.

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

---

## ⚖️ Architectural Trade-offs

To balance security, maintainability, and delivery speed, several conscious trade-offs were made during development:

1. **`eval()` vs. Custom Parser:** We used Python's `eval()` for rule execution. *Trade-off:* While `eval()` introduces theoretical security risks, we mitigated this by stripping the `__builtins__` context and running a strict AST (Abstract Syntax Tree) validation pass at startup. This provided maximum flexibility for business operators to write logic without the engineering overhead of building a custom grammar parser.
2. **JSON vs. XML for Batch Uploads:** We chose JSON over XML for the batch endpoint. *Trade-off:* While some legacy logistics systems rely on XML, JSON integrates natively with FastAPI/Pydantic, has a smaller payload size, and completely eliminates the risk of XXE (XML External Entity) injection attacks.
3. **In-Memory Rules vs. Database:** Rules are loaded into memory from a YAML file at startup. *Trade-off:* This means the server must be restarted (or a webhook triggered) to apply new rules. However, it guarantees zero database latency during the critical path of parcel evaluation.

---

## 🛠️ Tech Stack
- **Backend:** Python 3.11, FastAPI, Uvicorn, Pydantic V2
- **Testing:** Pytest, AnyIO
- **Frontend:** HTML5, JavaScript, Tailwind CSS (via CDN)
- **CI/CD:** GitHub Actions

---

## 🚦 Getting Started

### Installation
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt