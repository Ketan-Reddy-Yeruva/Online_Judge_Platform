import os
import datetime
import subprocess
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # <-- THIS WAS THE MISSING PIECE!
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# 1. DATABASE CONFIGURATION
DATABASE_URL = "postgresql://judge_admin:password123@localhost/judge_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. DATABASE MODELS
class DBProblem(Base):
    __tablename__ = "problems"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    time_limit = Column(Integer, default=2)

class DBSubmission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer)
    code = Column(Text)
    verdict = Column(String, default="Pending")
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)

# Automatically generate tables inside PostgreSQL
Base.metadata.create_all(bind=engine)

# Database session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 3. FASTAPI APP & CORS SETUP
app = FastAPI(title="Online Judge Platform Backend")

# Allow the React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. SCHEMAS
class ProblemCreate(BaseModel):
    title: str
    description: str
    time_limit: int = 2

class SubmissionRequest(BaseModel):
    problem_id: int
    source_code: str
    input_data: str
    expected_output: str

# 5. API ENDPOINTS
@app.post("/problems")
def create_problem(prob: ProblemCreate, db: Session = Depends(get_db)):
    new_prob = DBProblem(title=prob.title, description=prob.description, time_limit=prob.time_limit)
    db.add(new_prob)
    db.commit()
    db.refresh(new_prob)
    return {"message": "Problem created!", "id": new_prob.id}

@app.get("/problems")
def list_problems(db: Session = Depends(get_db)):
    return db.query(DBProblem).all()

@app.post("/submit")
async def evaluate_code(req: SubmissionRequest, db: Session = Depends(get_db)):
    # Record submission to PostgreSQL
    new_sub = DBSubmission(problem_id=req.problem_id, code=req.source_code, verdict="Judging")
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)

    # Write files to run compilation
    with open("temp.cpp", "w") as f: f.write(req.source_code)
    with open("temp_in.txt", "w") as f: f.write(req.input_data)

    # Compile
    compile_res = subprocess.run(["g++", "temp.cpp", "-o", "sol.out"], capture_output=True, text=True)
    if compile_res.returncode != 0:
        new_sub.verdict = "Compilation Error (CE)"
        db.commit()
        return {"verdict": new_sub.verdict, "error": compile_res.stderr}

    # Run execution
    try:
        with open("temp_in.txt", "r") as infile:
            # Note: I fixed the timeout bug here by hardcoding it to 2.0 seconds
            run_res = subprocess.run(["./sol.out"], stdin=infile, capture_output=True, text=True, timeout=2.0)
            
            if run_res.returncode != 0:
                new_sub.verdict = "Runtime Error (RE)"
            elif run_res.stdout.strip() == req.expected_output.strip():
                new_sub.verdict = "Accepted (AC) ✅"
            else:
                new_sub.verdict = "Wrong Answer (WA) ❌"
                
            db.commit()
            return {"verdict": new_sub.verdict}
            
    except subprocess.TimeoutExpired:
        new_sub.verdict = "Time Limit Exceeded (TLE) ⏰"
        db.commit()
        return {"verdict": new_sub.verdict}
        
    finally:
        # File Cleanup
        for f in ["temp.cpp", "temp_in.txt", "sol.out"]:
            if os.path.exists(f): os.remove(f)