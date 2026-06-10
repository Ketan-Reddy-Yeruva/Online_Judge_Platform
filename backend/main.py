from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Import our database tools from our new database.py file!
from database import SessionLocal, DBProblem, DBSubmission, DBTestCase

# Import our background processing task from worker.py
from worker import execute_grading_gauntlet

# Database session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FASTAPI APP & CORS SETUP
app = FastAPI(title="Online Judge Platform Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SCHEMAS
class ProblemCreate(BaseModel):
    title: str
    description: str
    time_limit: int = 2

class SubmissionRequest(BaseModel):
    problem_id: int
    source_code: str
    
class TestCaseCreate(BaseModel):
    problem_id: int
    input_data: str
    expected_output: str

# API ENDPOINTS
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
    problem = db.query(DBProblem).filter(DBProblem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem

@app.post("/submit")
async def evaluate_code(req: SubmissionRequest, db: Session = Depends(get_db)):
    # 1. Instantly record submission to PostgreSQL as "Pending"
    new_sub = DBSubmission(problem_id=req.problem_id, code=req.source_code, verdict="Pending")
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)

    # 2. Fire-and-forget: Push the job metadata to Redis queue for Celery workers
    execute_grading_gauntlet.delay(new_sub.id, req.problem_id, req.source_code)

    # 3. Instantly respond to the user browser
    return {
        "message": "Submission queued successfully!", 
        "submission_id": new_sub.id, 
        "verdict": "Pending"
    }

@app.get("/submission/status/{submission_id}")
def get_submission_status(submission_id: int, db: Session = Depends(get_db)):
    submission = db.query(DBSubmission).filter(DBSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return {"verdict": submission.verdict}