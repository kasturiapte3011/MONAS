# Multi Objective Neural Architecture Search
## How to run ?
1. Create two terminals, one for frontend and one for the backend.

2. TO RUN THE FRONTEND:
From the repository root:

```bash
cd frontend
HOST=127.0.0.1 PORT=3000 BROWSER=none npm start
```

3. TO RUN THE BACKEND:

From the repository root:

```bash
backend_modules/.venv/bin/python -m uvicorn backend_modules.main:app --reload --host 127.0.0.1 --port 8000
```