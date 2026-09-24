# AI Collaboration Log: Prompts & Problems Solved

This project was developed iteratively using AI as a pair-programming partner. Below is a summary of the core engineering problems faced and the prompts used to guide the architectural decisions.

## 1. Core Architecture & Validation
**Problem:** Raw JSON parsing in Python can be vulnerable to Billion Laughs attacks, null byte injections, and XSS if passed directly to models.
*   **Prompt Theme:** "How do I implement custom JSON parsing in Python to block null bytes, strip HTML/XSS tags, and prevent deeply nested payload attacks before handing data to Pydantic?"
*   **Result:** Created `app/routing/parsing.py` as a strict isolation layer.

## 2. Dynamic Rule Engine (The Sandbox)
**Problem:** Hardcoding routing rules requires deployments for every business logic change. We needed a dynamic but safe execution environment.
*   **Prompt Theme:** "Design a sandboxed evaluation engine in Python that safely executes mathematical and logical conditions loaded from a YAML file."
*   **Result:** Developed `engine.py` utilizing Python's `eval()` restricted strictly to `__builtins__: {}` and a tightly controlled context dictionary based on the Pydantic schema.

## 3. Observability & Logging
**Problem:** Traditional logs are hard to search in production and might leak sensitive user data like emails or credit cards.
*   **Prompt Theme:** "Write a Python logging formatter that outputs pure JSON, injects a ContextVar-based Request ID, and uses regex to automatically redact PII (emails/cards) from all log messages."
*   **Result:** Implemented `app/core/logging.py` alongside a global exception handler in `errors.py` that logs full tracebacks internally but returns sterile 500 responses to clients.

## 4. Middleware & Boundary Security
**Problem:** The API needs to handle malicious traffic, massive payloads, and rapid-fire requests without crashing.
*   **Prompt Theme:** "Provide production-grade FastAPI middlewares for custom API Key verification, IP-based rate limiting, payload size enforcement, and OWASP security headers."
*   **Result:** Created `app/core/security.py` protecting the main `/route` endpoint and generating traffic metrics.

## 5. User Interface
**Problem:** End-users and operators need a visual way to interact with the engine and understand its decisions without reading raw JSON.
*   **Prompt Theme:** "Create a single-file interactive dashboard using HTML and Tailwind CSS that connects to a FastAPI backend, handles custom headers (API Key), and renders a beautiful decision card or error state based on the HTTP response."
*   **Result:** Built `app/static/index.html` to serve as a clean, responsive frontend directly from FastAPI.