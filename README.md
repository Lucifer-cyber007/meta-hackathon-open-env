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

<div align="center">

# 🔍 CodeReviewEnv

### An OpenEnv-Compliant Environment for AI Code Review Agents

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compliant-purple)](https://github.com/open-env)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

*Train and evaluate AI agents on **real-world code review tasks** — identifying bugs, security vulnerabilities, performance pitfalls, and logic errors in production-style code.*

</div>

---

## 🎯 What is CodeReviewEnv?

Code review is one of the highest-value tasks a senior software engineer performs daily. It demands pattern recognition across multiple domains — spotting subtle bugs, security flaws, race conditions, and architectural issues — all within dense, real-world code.

**CodeReviewEnv** is a fully OpenEnv-compliant reinforcement learning environment that simulates this workflow end-to-end:

1. An **agent receives a code diff** (pull request) as an observation
2. The agent must produce **structured review comments** — identifying issues by line number, type, and severity
3. The agent issues a **final verdict** (`approve` / `request_changes` / `comment`)
4. A **deterministic grader** scores the episode with dense, shaped rewards

This fills a critical gap in the OpenEnv ecosystem: **no existing environment trains agents on structured, multi-criteria code analysis with dense reward feedback.**

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Server                        │
│                   (app.py — port 7860)                   │
├──────────┬──────────┬──────────┬──────────┬──────────────┤
│  /reset  │  /step   │  /state  │  /tasks  │  /grader     │
├──────────┴──────────┴──────────┴──────────┴──────────────┤
│              CodeReviewEnv (environment.py)              │
│         Gym-style: reset() → observe → step() → reward  │
├─────────────────────────────────────────────────────────┤
│  tasks.py          │  graders.py       │  models.py      │
│  3 curated diffs   │  Deterministic    │  Pydantic       │
│  with known issues │  scoring engine   │  Action/Obs     │
├─────────────────────────────────────────────────────────┤
│              inference.py (Baseline Agent)               │
│         Gemini 2.0 Flash via OpenAI-compatible API      │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Tasks — 3 Difficulty Levels

CodeReviewEnv ships with **3 hand-crafted tasks** of escalating difficulty, each targeting different code review skills:

### Task 1 — 🟢 Easy: Basic Bug Detection

| Property | Value |
|---|---|
| **File** | `utils/statistics.py` |
| **Known Issues** | 3 critical bugs (ZeroDivisionError, IndexError), 1 performance issue |
| **Max Steps** | 3 |
| **Success Threshold** | 0.60 |
| **What It Tests** | Edge-case reasoning, basic Python bug detection |
| **Expected Behavior** | A competent LLM should find most issues on the first pass |

### Task 2 — 🟡 Medium: Security Vulnerability Review

| Property | Value |
|---|---|
| **File** | `auth/user_manager.py` |
| **Known Issues** | 7 security vulnerabilities |
| **Vulnerability Types** | SQL injection ×2, hardcoded secrets ×2, MD5 hashing, pickle deserialization, permission logic bug |
| **Max Steps** | 5 |
| **Success Threshold** | 0.45 |
| **What It Tests** | Security domain knowledge, OWASP awareness |
| **Expected Behavior** | Requires specialized security knowledge; generic models miss subtle flaws |

### Task 3 — 🔴 Hard: Concurrency & Architecture Bug Hunt

| Property | Value |
|---|---|
| **File** | `core/rate_limiter.py` |
| **Known Issues** | 7 bugs (race conditions, dictionary mutation during iteration, silent exceptions, thread join issues, architecture flaws) |
| **Max Steps** | 8 |
| **Success Threshold** | 0.35 |
| **What It Tests** | Deep concurrency expertise, threading pitfalls, systems-level reasoning |
| **Expected Behavior** | **Genuinely challenges frontier models** — even GPT-4o struggles with subtle race conditions |

---

## 🎁 Reward Function Design

Rewards are **dense and shaped** over the full trajectory — not just a binary end-of-episode signal. This enables meaningful gradient signal for RL training:

| Signal | Reward | Rationale |
|---|---|---|
| ✅ Correctly identified **critical** issue | **+0.20** | High-value finds deserve strong positive signal |
| ✅ Correctly identified **major** issue | **+0.12** | Important but less impactful than critical |
| ✅ Correctly identified **minor** issue | **+0.05** | Still valuable, but lower reward to avoid noise |
| ❌ **False positive** comment | **−0.08** | Penalizes hallucinated issues — precision matters |
| ✅ Correct **verdict** | **+0.10** | Approve vs. request_changes alignment |
| ❌ Wrong **verdict** | **−0.15** | Wrong verdict is a costly mistake |
| ⏱️ **Step penalty** (efficiency) | **−0.02** per step | Encourages agents to find issues quickly |

**Reward range:** `[-1.0, 1.0]` — clamped and normalized for stable training.

### Design Philosophy

- **Precision over recall**: False positives are penalized harder than missed issues are unrewarded, encouraging agents to be confident before flagging
- **Severity-weighted**: Critical findings earn 4× the reward of minor ones, teaching agents to prioritize
- **Efficiency bonus**: Step penalties incentivize single-pass accuracy over iterative guessing

---

## 📊 Baseline Scores

Measured with **Gemini 2.0 Flash**, `temperature=0`:

| Task | Difficulty | Baseline Score | Threshold |
|---|---|---|---|
| Basic Bug Detection | 🟢 Easy | **0.95** | 0.60 |
| Security Vulnerability Review | 🟡 Medium | **0.90** | 0.45 |
| Concurrency & Architecture | 🔴 Hard | **0.29** | 0.35 |
| **Weighted Average** | — | **0.71** | — |

> **Key Insight:** The hard task is genuinely challenging — even with a strong model, the agent only achieves 0.29/1.0 on concurrency bugs. This demonstrates the environment's value as a training signal for improving AI code review capabilities.

---

## 🔌 API Endpoints

All endpoints follow the [OpenEnv specification](https://github.com/open-env):

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check — returns status and available endpoints |
| `POST` | `/reset` | Reset environment to a clean state; returns initial observation |
| `POST` | `/step` | Submit a review action; returns observation, reward, done, info |
| `GET` | `/state` | Get current environment state |
| `GET` | `/tasks` | List all tasks with action schema |
| `POST` | `/grader` | Score a completed episode (deterministic) |
| `POST` | `/baseline` | Run baseline inference across all tasks |

### Observation Space

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

### Action Space

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

### Quick Test

```bash
# Reset environment (easy task)
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy"}'

# Submit a review action
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

# List all tasks
curl http://localhost:7860/tasks

# Get current state
curl http://localhost:7860/state
```

---

## 🚀 Setup & Usage

### Local Development

```bash
# Clone the repo
git clone https://github.com/Lucifer-cyber007/meta-hackathon-open-env
cd meta-hackathon-open-env

# Install dependencies
pip install -r requirements.txt

# Set your API key
export GEMINI_API_KEY=your_key_here

# Run the server
python app.py
# or
uvicorn app:app --host 0.0.0.0 --port 7860 --reload
```

Server starts at `http://localhost:7860`

### Docker

```bash
# Build
docker build -t code-review-env .

# Run
docker run -p 7860:7860 -e GEMINI_API_KEY=your_key_here code-review-env
```

### Run Baseline Inference

```bash
export GEMINI_API_KEY=your_key_here

# Run all 3 tasks
python inference.py

# Run a single task
python inference.py --task easy

# Use a different model
python inference.py --model gemini-2.0-flash
```

### Deploy to Hugging Face Spaces

1. Create a new Space on [huggingface.co](https://huggingface.co) with **Docker** SDK
2. Tag your Space with `openenv`
3. Push your code:
```bash
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/code-review-env
git push hf main
```
4. Set `GEMINI_API_KEY` in Space Settings → Repository Secrets

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| **Web Framework** | [FastAPI](https://fastapi.tiangolo.com) with Uvicorn ASGI server |
| **Data Validation** | [Pydantic v2](https://docs.pydantic.dev) — strict typing for all API models |
| **LLM Provider** | [Google Gemini 2.0 Flash](https://ai.google.dev) via OpenAI-compatible API |
| **Containerization** | Docker (Hugging Face Spaces compatible) |
| **Environment Design** | OpenAI Gym-style `reset()` / `step()` / `state()` interface |
| **Grading** | Deterministic, reproducible scoring — no LLM-as-judge |
| **Language** | Python 3.10+ |

---

## 📁 Project Structure

```
code-review-env/
├── app.py             # FastAPI server — all HTTP endpoints
├── environment.py     # Core env logic: reset() / step() / state()
├── models.py          # Pydantic models: Observation, Action, Reward
├── tasks.py           # Task definitions with code diffs & known issues
├── graders.py         # Deterministic graders returning 0.0–1.0
├── inference.py       # Gemini-based baseline inference script
├── baseline.py        # Legacy baseline runner
├── openenv.yaml       # OpenEnv spec metadata
├── Dockerfile         # Container build for HF Spaces
├── requirements.txt   # Pinned dependencies
└── README.md          # You are here
```

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built for the Meta PyTorch Hackathon × Scaler School of Technology**

*CodeReviewEnv — teaching AI agents to review code like senior engineers* 🚀

</div>
