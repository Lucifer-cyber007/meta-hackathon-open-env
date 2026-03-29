"""
Quick diagnostic: test all imports and run baseline for 'easy' task.
"""
import sys
import traceback

print("Python:", sys.version)
print("Testing imports...")

try:
    from openai import OpenAI
    print("[OK] openai")
except ImportError as e:
    print(f"[FAIL] openai: {e}")

try:
    from environment import CodeReviewEnv
    print("[OK] environment")
except Exception as e:
    print(f"[FAIL] environment: {e}")
    traceback.print_exc()

try:
    from graders import grade_episode
    print("[OK] graders")
except Exception as e:
    print(f"[FAIL] graders: {e}")
    traceback.print_exc()

try:
    from models import Action, CodeComment, GraderInput
    print("[OK] models")
except Exception as e:
    print(f"[FAIL] models: {e}")
    traceback.print_exc()

print("\nAll import checks done.")

# Now try running the actual baseline
try:
    import baseline
    # Override sys.argv to simulate --task easy
    sys.argv = ["baseline.py", "--task", "easy"]
    baseline.main()
except Exception as e:
    print(f"\n[ERROR in main]: {e}")
    traceback.print_exc()
