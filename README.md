---
title: CodeReviewEnv
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
tags:
  - openenv
---

# CodeReviewEnv

> An OpenEnv-compliant environment for training and evaluating AI agents on **real-world code review tasks**.

---

## Environment Description & Motivation

Software code review is one of the highest-value tasks a senior engineer performs daily. It requires identifying bugs, spotting security vulnerabilities, understanding intent, and giving actionable feedback — all skills that current AI agents struggle to do reliably.

**CodeReviewEnv** simulates this workflow: an agent receives a code diff (pull request) and must produce structured review comments identifying issues by line number, type, and severity, then issue a final verdict (approve / request_changes).

This fills a real gap in the OpenEnv ecosystem: no existing environment trains agents on structured, multi-criteria code analysis with dense reward feedback.

---

## Action Space

The agent submits an `Action` object at each step:

```json
{
  "comments": [
    {
      "line_number": 5,
      "issue_type": "bug",
      "severity": "critical",
      "description": "ZeroDivisionError when numbers list is empty",
      "suggested_fix": "Add: if not numbers: return 0.0"
    }
  ],
  "verdict": "request_changes",
  "summary": "This PR has 3 critical bugs that must be fixed before merging."
}
```

| Field | Type | Values |
|---|---|---|
| `comments[].line_number` | `int` | 1-indexed line number in the diff |
| `comments[].issue_type` | `string` | `bug`, `security`, `performance`, `style`, `logic` |
| `comments[].severity` | `string` | `critical`, `major`, `minor` |
| `comments[].description` | `string` | Free-text description of the issue |
| `comments[].suggested_fix` | `string?` | Optional suggested fix |
| `verdict` | `string` | `approve`, `request_changes`, `comment` |
| `summary` | `string?` | Optional overall review summary |

---

## Observation Space

The agent receives an `Observation` at each step:

```json
{
  "diff": "--- a/utils/statistics.py\n+++ b/utils/statistics.py\n...",
  "file_name": "utils/statistics.py",
  "pr_title": "Add calculate_statistics utility module",
  "pr_description": "Adding utility functions for the analytics dashboard.",
  "step_number": 1,
  "max_steps": 3,
  "task_id": "easy",
  "task_description": "Review a simple Python utility module. Find edge case bugs..."
}
```

| Field | Type | Description |
|---|---|---|
| `diff` | `string` | Unified diff format patch |
| `file_name` | `string` | File being reviewed |
| `pr_title` | `string` | Pull request title |
| `pr_description` | `string` | PR author's description |
| `step_number` | `int` | Current step (resets on `reset()`) |
| `max_steps` | `int` | Steps budget for this task |
| `task_id` | `string` | `easy`, `medium`, or `hard` |
| `task_description` | `string` | Task objective description |

---

## Reward Function

Reward is shaped over the **full trajectory** — not just binary end-of-episode signal:

| Signal | Value |
|---|---|
| Correctly identified critical issue | +0.20 |
| Correctly identified major issue | +0.12 |
| Correctly identified minor issue | +0.05 |
| False positive comment | -0.08 |
| Correct verdict (approve/request_changes) | +0.10 |
| Wrong verdict | -0.15 |
| Step penalty (efficiency) | -0.02 per step |

Range: **[-1.0, 1.0]**

---

## Tasks

### Task 1 — Easy: Basic Bug Detection
- **File**: `utils/statistics.py`
- **Known Issues**: 3 critical bugs (ZeroDivisionError, IndexError), 1 performance issue
- **Max Steps**: 3
- **Success Threshold**: 0.60
- **Expected Difficulty**: A competent LLM should find most issues

### Task 2 — Medium: Security Vulnerability Review
- **File**: `auth/user_manager.py`
- **Known Issues**: 7 security vulnerabilities (SQL injection ×2, hardcoded secrets ×2, MD5 hashing, pickle deserialization, permission logic bug)
- **Max Steps**: 5
- **Success Threshold**: 0.45
- **Expected Difficulty**: Requires security domain knowledge

### Task 3 — Hard: Concurrency & Architecture Bug Hunt
- **File**: `core/rate_limiter.py`
- **Known Issues**: 7 bugs (race conditions, dictionary mutation during iteration, silent exceptions, thread join, architecture flaws)
- **Max Steps**: 8
- **Success Threshold**: 0.35
- **Expected Difficulty**: Requires deep concurrency expertise, genuinely challenges frontier models

---

## Setup & Usage

### Local Development

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/code-review-env
cd code-review-env

# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
# or
uvicorn app:app --host 0.0.0.0 --port 7860 --reload
```

Server starts at `http://localhost:7860`

### Quick API Test

```bash
# Reset environment (easy task)
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy"}'

# Submit an action
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{
    "comments": [
      {
        "line_number": 5,
        "issue_type": "bug",
        "severity": "critical",
        "description": "ZeroDivisionError when numbers list is empty",
        "suggested_fix": "Check if not numbers before dividing"
      }
    ],
    "verdict": "request_changes",
    "summary": "Found a critical division by zero bug"
  }'

# Get all tasks
curl http://localhost:7860/tasks

# Get current state
curl http://localhost:7860/state
```

### Docker

```bash
# Build
docker build -t code-review-env .

# Run
docker run -p 7860:7860 -e OPENAI_API_KEY=your_key_here code-review-env
```

### Run Baseline Script

```bash
export OPENAI_API_KEY=your_key_here

# Run all 3 tasks
python baseline.py

# Run single task
python baseline.py --task easy

# Use a different model
python baseline.py --model gpt-4o
```

### Deploy to Hugging Face Spaces

1. Create a new Space on huggingface.co with **Docker** SDK
2. Tag your Space with `openenv`
3. Push your code:
```bash
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/code-review-env
git push hf main
```
4. Set `OPENAI_API_KEY` in Space Settings → Repository Secrets

---

## Baseline Scores

Measured with `gpt-4o-mini`, `temperature=0`, `seed=42`:

| Task | Difficulty | Score |
|---|---|---|
| Basic Bug Detection | Easy | ~0.65 |
| Security Vulnerability Review | Medium | ~0.45 |
| Concurrency & Architecture Bug Hunt | Hard | ~0.30 |

*Run `python baseline.py` with your own API key to reproduce.*

---

## Project Structure

```
code-review-env/
├── app.py           # FastAPI app — all HTTP endpoints
├── environment.py   # Core env logic: step() / reset() / state()
├── models.py        # Pydantic models: Observation, Action, Reward
├── tasks.py         # Task definitions with code diffs & known issues
├── graders.py       # Deterministic graders returning 0.0–1.0
├── reward.py        # Reward shaping with partial progress signals
├── baseline.py      # OpenAI-based baseline inference script
├── openenv.yaml     # OpenEnv spec metadata
├── Dockerfile       # Container build
├── requirements.txt # Pinned dependencies
└── README.md        # This file
```
