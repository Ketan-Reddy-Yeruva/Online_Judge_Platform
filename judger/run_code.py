import subprocess
import os

def compile_code(source_file, executable_name):
    """Compiles the C++ source code."""
    print(f"Compiling {source_file}...")
    
    # The command we want Python to run: g++ dummy_solution.cpp -o solution.out
    compile_command = ["g++", source_file, "-o", executable_name]
    
    try:
        # run() executes the command. capture_output saves any compiler errors.
        result = subprocess.run(compile_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Compilation Successful!\n")
            return True
        else:
            print("Compilation Error:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"Failed to run compiler: {e}")
        return False

def run_and_evaluate(executable_name, input_file, expected_output_file):
    """Runs the executable, feeds it input, and compares the output."""
    print("Running execution phase...")
    
    # Read the expected output
    with open(expected_output_file, 'r') as f:
        expected_output = f.read().strip()
        
    try:
        # Open the input file to pass into the program
        with open(input_file, 'r') as infile:
            # Run the compiled program. timeout=2 handles Time Limit Exceeded (TLE)
            result = subprocess.run(
                [f"./{executable_name}"],
                stdin=infile,
                capture_output=True,
                text=True,
                timeout=2.0 
            )
            
            # Check for Runtime Errors (like segfaults or return 1)
            if result.returncode != 0:
                print("Verdict: Runtime Error (RE)")
                print(result.stderr)
                return
                
            actual_output = result.stdout.strip()
            
            # Evaluate
            if actual_output == expected_output:
                print("Verdict: Accepted (AC) ✅")
            else:
                print(f"Verdict: Wrong Answer (WA) ❌")
                print(f"Expected: '{expected_output}', Got: '{actual_output}'")
                
    except subprocess.TimeoutExpired:
        print("Verdict: Time Limit Exceeded (TLE) ⏰")
    except Exception as e:
        print(f"System Error: {e}")

if __name__ == "__main__":
    source = "dummy_solution.cpp"
    executable = "solution.out"
    in_file = "input.txt"
    out_file = "expected_output.txt"
    
    if compile_code(source, executable):
        run_and_evaluate(executable, in_file, out_file)
        
    # Clean up the compiled binary
    if os.path.exists(executable):
        os.remove(executable)