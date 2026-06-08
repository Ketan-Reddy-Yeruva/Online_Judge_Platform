# AlgoJudge: Full-Stack Online Code Evaluator

A scalable, full-stack Online Judge platform (similar to Codeforces or LeetCode) built to compile, execute, and evaluate C++ source code against dynamic test cases. 

## 🏗️ Architecture & Tech Stack

* **Frontend:** React (Vite), Monaco Editor, React Router, Axios
* **Backend:** Python, FastAPI, Uvicorn
* **Database:** PostgreSQL, SQLAlchemy (ORM)
* **Execution Engine:** Native C++ (`g++`), Subprocess Management

## ✨ Current Features (v1.0)

* **Dynamic Problem Dashboard:** Fetches and displays available coding challenges directly from the PostgreSQL database.
* **Integrated Web IDE:** Features a fully functional VS Code-style editor powered by Monaco, complete with syntax highlighting and formatting.
* **Real-Time Evaluation:** Submits user code to the FastAPI backend, compiles it on the fly, evaluates it against expected inputs/outputs, and returns standard judge verdicts (e.g., `Accepted (AC) ✅`, `Wrong Answer (WA) ❌`, `Compilation Error (CE)`).
* **Time Complexity Guards:** Implements strict backend execution timeouts to catch infinite loops and return `Time Limit Exceeded (TLE) ⏰`.

## 🚀 Local Setup (WSL / Ubuntu)

### 1. Database Setup
Ensure PostgreSQL is installed and running on port `5432`. Create a database and user:
```sql
CREATE DATABASE judge_db;
CREATE USER judge_admin WITH PASSWORD 'password123';
GRANT ALL PRIVILEGES ON DATABASE judge_db TO judge_admin;
```

### 2. Backend Setup
Navigate to the backend directory, install requirements, and boot the FastAPI server:
```bash
cd backend
pip install fastapi uvicorn sqlalchemy psycopg2-binary
uvicorn main:app --reload
```

### 3. Frontend Setup
Navigate to the frontend directory, install dependencies, and start the Vite development server:
```bash
cd frontend
npm install
npm run dev
```

## 🗺️ Roadmap (Upcoming Features)

- [ ] **Docker Sandboxing:** Wrap the execution engine in ephemeral, restricted Docker containers to prevent malicious code execution.
- [ ] **Asynchronous Task Queue:** Implement Redis and Celery to handle multiple concurrent submissions without blocking the main API thread.
- [ ] **Expanded Language Support:** Add support for Python and Java compilation.