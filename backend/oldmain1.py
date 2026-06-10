import os
import datetime
import subprocess
import uuid
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # <-- THIS WAS THE MISSING PIECE!
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import ForeignKey # Add this to your sqlalchemy imports at the top!

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

class DBTestCase(Base):
    __tablename__ = "test_cases"
    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"))
    input_data = Column(Text)
    expected_output = Column(Text)
    is_hidden = Column(Boolean, default=False)

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
    # Removed input_data and expected_output!
    
class TestCaseCreate(BaseModel):
    problem_id: int
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

@app.post("/testcases")
def create_test_case(tc: TestCaseCreate, db: Session = Depends(get_db)):
    new_tc = DBTestCase(
        problem_id=tc.problem_id, 
        input_data=tc.input_data, 
        expected_output=tc.expected_output
    )
    db.add(new_tc)
    db.commit()
    return {"message": "Test case added securely!"}

@app.get("/problems")
def list_problems(db: Session = Depends(get_db)):
    return db.query(DBProblem).all()

@app.get("/problems/{problem_id}")
def get_single_problem(problem_id: int, db: Session = Depends(get_db)):
    # Query PostgreSQL for the specific ID
    problem = db.query(DBProblem).filter(DBProblem.id == problem_id).first()
    
    # If someone types a random ID in the URL that doesn't exist, throw a 404
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
        
    return problem

@app.post("/submit")
async def evaluate_code(req: SubmissionRequest, db: Session = Depends(get_db)):
    # 1. Fetch all secret test cases for this problem
    test_cases = db.query(DBTestCase).filter(DBTestCase.problem_id == req.problem_id).all()
    if not test_cases:
        return {"verdict": "System Error: No test cases found for this problem!"}

    new_sub = DBSubmission(problem_id=req.problem_id, code=req.source_code, verdict="Judging")
    db.add(new_sub)
    db.commit()

    submission_id = str(uuid.uuid4())
    work_dir = os.path.abspath(f"./submissions/{submission_id}")
    os.makedirs(work_dir, exist_ok=True)

    with open(f"{work_dir}/temp.cpp", "w") as f: f.write(req.source_code)

    try:
        # 2. Compile the code exactly once
        compile_cmd = [
            "docker", "run", "--rm", "-v", f"{work_dir}:/usr/src/app", 
            "-w", "/usr/src/app", "gcc:latest", "g++", "temp.cpp", "-o", "sol.out"
        ]
        compile_res = subprocess.run(compile_cmd, capture_output=True, text=True)
        
        if compile_res.returncode != 0:
            new_sub.verdict = "Compilation Error (CE)"
            db.commit()
            return {"verdict": new_sub.verdict, "error": compile_res.stderr}

        # 3. THE GAUNTLET: Loop through every test case
        for idx, tc in enumerate(test_cases, start=1):
            # Write this specific test case's input to the sandbox
            with open(f"{work_dir}/temp_in.txt", "w") as f: f.write(tc.input_data)
            
            run_cmd = [
                "docker", "run", "--rm", "-v", f"{work_dir}:/usr/src/app", 
                "-w", "/usr/src/app", "gcc:latest", "sh", "-c", "./sol.out < temp_in.txt"
            ]
            run_res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=10.0)
            
            if run_res.returncode != 0:
                new_sub.verdict = f"Runtime Error (RE) on Test {idx}"
                db.commit()
                return {"verdict": new_sub.verdict}
                
            if run_res.stdout.strip() != tc.expected_output.strip():
                new_sub.verdict = f"Wrong Answer (WA) on Test {idx} ❌"
                db.commit()
                return {"verdict": new_sub.verdict}
        
        # If it survives the loop without returning, it passed everything!
        new_sub.verdict = "Accepted (AC) ✅"
        db.commit()
        return {"verdict": new_sub.verdict}
            
    except subprocess.TimeoutExpired:
        new_sub.verdict = "Time Limit Exceeded (TLE) ⏰"
        db.commit()
        return {"verdict": new_sub.verdict}

# @app.post("/submit")
# async def evaluate_code(req: SubmissionRequest, db: Session = Depends(get_db)):
#     # Record submission to PostgreSQL
#     new_sub = DBSubmission(problem_id=req.problem_id, code=req.source_code, verdict="Judging")
#     db.add(new_sub)
#     db.commit()
#     db.refresh(new_sub)

#     # 1. Create a unique folder for THIS specific submission to prevent overlaps
#     submission_id = str(uuid.uuid4())
#     work_dir = os.path.abspath(f"./submissions/{submission_id}")
#     os.makedirs(work_dir, exist_ok=True)

#     # Write files to the unique folder
#     with open(f"{work_dir}/temp.cpp", "w") as f: f.write(req.source_code)
#     with open(f"{work_dir}/temp_in.txt", "w") as f: f.write(req.input_data)

#     try:
#         # 2. Compile INSIDE the Docker Sandbox
#         compile_cmd = [
#             "docker", "run", "--rm", 
#             "-v", f"{work_dir}:/usr/src/app", 
#             "-w", "/usr/src/app", 
#             "gcc:latest", 
#             "g++", "temp.cpp", "-o", "sol.out"
#         ]
#         compile_res = subprocess.run(compile_cmd, capture_output=True, text=True)
        
#         if compile_res.returncode != 0:
#             new_sub.verdict = "Compilation Error (CE)"
#             return {"verdict": new_sub.verdict, "error": compile_res.stderr}

#         # 3. Execute INSIDE the Docker Sandbox (with a strict 2-second timeout!)
#         run_cmd = [
#             "docker", "run", "--rm", 
#             "-v", f"{work_dir}:/usr/src/app", 
#             "-w", "/usr/src/app", 
#             "gcc:latest", 
#             "sh", "-c", "./sol.out < temp_in.txt"
#         ]
#         run_res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=10.0)
        
#         if run_res.returncode != 0:
#             new_sub.verdict = "Runtime Error (RE)"
#         elif run_res.stdout.strip() == req.expected_output.strip():
#             new_sub.verdict = "Accepted (AC) ✅"
#         else:
#             new_sub.verdict = "Wrong Answer (WA) ❌"
            
#     except subprocess.TimeoutExpired:
#         new_sub.verdict = "Time Limit Exceeded (TLE) ⏰"
        
#     finally:
#         # 4. Clean up the files, but keep the database record
#         db.commit()
#         # Optionally, you can delete the folder here to save space
        
#     return {"verdict": new_sub.verdict}

# @app.post("/submit")
# async def evaluate_code(req: SubmissionRequest, db: Session = Depends(get_db)):
#     # Record submission to PostgreSQL
#     new_sub = DBSubmission(problem_id=req.problem_id, code=req.source_code, verdict="Judging")
#     db.add(new_sub)
#     db.commit()
#     db.refresh(new_sub)

#     # Write files to run compilation
#     with open("temp.cpp", "w") as f: f.write(req.source_code)
#     with open("temp_in.txt", "w") as f: f.write(req.input_data)

#     # Compile
#     compile_res = subprocess.run(["g++", "temp.cpp", "-o", "sol.out"], capture_output=True, text=True)
#     if compile_res.returncode != 0:
#         new_sub.verdict = "Compilation Error (CE)"
#         db.commit()
#         return {"verdict": new_sub.verdict, "error": compile_res.stderr}

#     # Run execution
#     try:
#         with open("temp_in.txt", "r") as infile:
#             # Note: I fixed the timeout bug here by hardcoding it to 2.0 seconds
#             run_res = subprocess.run(["./sol.out"], stdin=infile, capture_output=True, text=True, timeout=2.0)
            
#             if run_res.returncode != 0:
#                 new_sub.verdict = "Runtime Error (RE)"
#             elif run_res.stdout.strip() == req.expected_output.strip():
#                 new_sub.verdict = "Accepted (AC) ✅"
#             else:
#                 new_sub.verdict = "Wrong Answer (WA) ❌"
                
#             db.commit()
#             return {"verdict": new_sub.verdict}
            
#     except subprocess.TimeoutExpired:
#         new_sub.verdict = "Time Limit Exceeded (TLE) ⏰"
#         db.commit()
#         return {"verdict": new_sub.verdict}
        
#     finally:
#         # File Cleanup
#         for f in ["temp.cpp", "temp_in.txt", "sol.out"]:
#             if os.path.exists(f): os.remove(f)