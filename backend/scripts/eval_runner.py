import subprocess
import time
import sys
import os
import json

def is_finished():
    checkpoint = os.path.join(os.path.dirname(__file__), "../../eval_results_checkpoint.json")
    if os.path.exists(checkpoint):
        with open(checkpoint, "r", encoding="utf-8") as f:
            data = json.load(f)
            # If we evaluated 100 questions, we're done
            if len(data.get("results", [])) >= 100:
                return True
    return False

def main():
    script_path = os.path.join(os.path.dirname(__file__), "eval_suite.py")
    
    attempts = 0
    while not is_finished() and attempts < 150:
        attempts += 1
        print(f"\n--- Starting runner loop attempt {attempts} ---")
        
        try:
            # We use timeout in case it hangs entirely (not just Python timeout)
            # 60s is enough for preloading + 1 eval. 
            # If it gets stuck entirely, the subprocess timeout will catch it.
            # But the Python script itself handles 45s generation timeouts, so we give it 300s here.
            subprocess.run([sys.executable, script_path], check=True, timeout=300)
            
            # If it finishes with exit code 0, check if we're done.
            if is_finished():
                print("\n--- Evaluation completed successfully! ---")
                break
                
        except subprocess.TimeoutExpired:
            print(f"\n--- Runner caught hard timeout. Restarting... ---")
            # Force kill python processes just in case
            subprocess.run("taskkill /F /IM python.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)
        except subprocess.CalledProcessError as e:
            print(f"\n--- Script exited with code {e.returncode}. Restarting... ---")
            time.sleep(2)

if __name__ == "__main__":
    main()
