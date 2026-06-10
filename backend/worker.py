import os
import uuid
import subprocess
from celery import Celery
from sqlalchemy.orm import Session

# Import from our new database file
from database import SessionLocal, DBSubmission, DBTestCase

# Changed variable to 'app' and fixed Redis port to 6379
app = Celery(
    "tasks",
    broker="redis://127.0.0.1:6379/0",
    backend="redis://127.0.0.1:6379/0"
)

@app.task
def execute_grading_gauntlet(submission_id: int, problem_id: int, source_code: str):
    db: Session = SessionLocal()
    try:
        submission = db.query(DBSubmission).filter(DBSubmission.id == submission_id).first()
        test_cases = db.query(DBTestCase).filter(DBTestCase.problem_id == problem_id).all()

        if not test_cases:
            submission.verdict = "System Error: No Test Cases"
            db.commit()
            return

        unique_id = str(uuid.uuid4())
        work_dir = os.path.abspath(f"./submissions/{unique_id}")
        os.makedirs(work_dir, exist_ok=True)

        with open(f"{work_dir}/temp.cpp", "w") as f: f.write(source_code)

# 1. Armored Compilation: Max 256MB RAM, Half CPU, NO Internet
        compile_cmd = [
            "docker", "run", "--rm", 
            "--memory=256m",  
            "--cpus=0.5",     
            "--network=none", 
            "-v", f"{work_dir}:/usr/src/app", 
            "-w", "/usr/src/app", "gcc:latest", "g++", "temp.cpp", "-o", "sol.out"
        ]
        compile_res = subprocess.run(compile_cmd, capture_output=True, text=True)
        
        if compile_res.returncode != 0:
            submission.verdict = "Compilation Error (CE)"
            db.commit()
            return

        for idx, tc in enumerate(test_cases, start=1):
            with open(f"{work_dir}/temp_in.txt", "w") as f: f.write(tc.input_data)
            
            # 2. Armored Execution: Max 128MB RAM, Prevent Fork Bombs (--pids-limit)
            run_cmd = [
                "docker", "run", "--rm", 
                "--memory=128m",   
                "--cpus=0.5",      
                "--pids-limit=64", 
                "--network=none",  
                "-v", f"{work_dir}:/usr/src/app", 
                "-w", "/usr/src/app", "gcc:latest", "sh", "-c", "./sol.out < temp_in.txt"
            ]
            run_res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=10.0)
            print(f"--- SECURITY LOG: Docker exited with code {run_res.returncode} ---")
        # compile_cmd = [
        #     "docker", "run", "--rm", "-v", f"{work_dir}:/usr/src/app", 
        #     "-w", "/usr/src/app", "gcc:latest", "g++", "temp.cpp", "-o", "sol.out"
        # ]
        # compile_res = subprocess.run(compile_cmd, capture_output=True, text=True)
        
        # if compile_res.returncode != 0:
        #     submission.verdict = "Compilation Error (CE)"
        #     db.commit()
        #     return

        # for idx, tc in enumerate(test_cases, start=1):
        #     with open(f"{work_dir}/temp_in.txt", "w") as f: f.write(tc.input_data)
            
        #     run_cmd = [
        #         "docker", "run", "--rm", "-v", f"{work_dir}:/usr/src/app", 
        #         "-w", "/usr/src/app", "gcc:latest", "sh", "-c", "./sol.out < temp_in.txt"
        #     ]
        #     run_res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=10.0)
            
            if run_res.returncode != 0:
                submission.verdict = f"Runtime Error (RE) on Test {idx}"
                db.commit()
                return
                
            if run_res.stdout.strip() != tc.expected_output.strip():
                submission.verdict = f"Wrong Answer (WA) on Test {idx} ❌"
                db.commit()
                return
        
        submission.verdict = "Accepted (AC) ✅"
        db.commit()

    except subprocess.TimeoutExpired:
        submission.verdict = "Time Limit Exceeded (TLE) ⏰"
        db.commit()
    except Exception as e:
        submission.verdict = f"System Error: {str(e)}"
        db.commit()
    finally:
        db.close()