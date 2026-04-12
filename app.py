"""
FastAPI application exposing the CodeReviewEnv via HTTP.

Endpoints:
  POST /reset         — reset environment, get initial observation
  POST /step          — submit an action, get observation + reward
  GET  /state         — get current environment state
  GET  /tasks         — list all tasks with action schema
  POST /grader        — score a completed episode
  POST /baseline      — run baseline inference and return scores
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Any, Dict, Optional
import os

from models import (
    Action,
    Observation,
    EnvironmentState,
    TaskInfo,
    GraderInput,
    GraderOutput,
)
from environment import CodeReviewEnv
from graders import grade_episode
from tasks import get_all_tasks

# ── App setup ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="CodeReviewEnv",
    description=(
        "An OpenEnv-compliant environment for training and evaluating AI agents "
        "on real-world code review tasks. Agents receive code diffs and must "
        "identify bugs, security issues, and quality problems."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single shared environment instance (stateful per session)
env = CodeReviewEnv()


# ── Request / Response schemas ────────────────────────────────────────────

# FIX 1: task_id is fully optional — works with empty POST body too
class ResetRequest(BaseModel):
    task_id: Optional[str] = "easy"

    model_config = {"extra": "allow"}


class StepResponse(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: Dict[str, Any]


class BaselineScore(BaseModel):
    task_id: str
    task_name: str
    difficulty: str
    score: float
    feedback: str


class BaselineResponse(BaseModel):
    scores: list[BaselineScore]
    model_used: str
    note: str


# ── Endpoints ─────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "environment": "CodeReviewEnv",
        "version": "1.0.0",
        "endpoints": ["/reset", "/step", "/state", "/tasks", "/grader", "/baseline"],
    }


# FIX 2: Accept completely empty body by making request optional
@app.post("/reset", response_model=Observation, tags=["OpenEnv"])
def reset(request: Optional[ResetRequest] = None):
    """Reset the environment to a clean state. Returns the initial observation."""
    try:
        task_id = request.task_id if request else "easy"
        obs = env.reset(task_id=task_id)
        return obs
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step", response_model=StepResponse, tags=["OpenEnv"])
def step(action: Action):
    """
    Submit an action to the environment.
    Returns the next observation, reward, done flag, and info dict.
    """
    try:
        obs, reward, done, info = env.step(action)
        return StepResponse(observation=obs, reward=reward, done=done, info=info)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/state", response_model=EnvironmentState, tags=["OpenEnv"])
def state():
    """Return the full current internal state of the environment."""
    return env.state()


@app.get("/tasks", tags=["OpenEnv"])
def tasks():
    """
    Return all available tasks with their action schema.
    Used by agents to discover what tasks exist and what actions are valid.
    """
    action_schema = {
        "type": "object",
        "required": ["verdict"],
        "properties": {
            "comments": {
                "type": "array",
                "description": "List of code review comments",
                "items": {
                    "type": "object",
                    "required": ["line_number", "issue_type", "severity", "description"],
                    "properties": {
                        "line_number": {"type": "integer", "description": "Line number (1-indexed)"},
                        "issue_type": {
                            "type": "string",
                            "enum": ["bug", "security", "performance", "style", "logic"],
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["critical", "major", "minor"],
                        },
                        "description": {"type": "string", "description": "Issue description"},
                        "suggested_fix": {"type": "string", "description": "Optional fix suggestion"},
                    },
                },
            },
            "verdict": {
                "type": "string",
                "enum": ["approve", "request_changes", "comment"],
                "description": "Final review verdict",
            },
            "summary": {
                "type": "string",
                "description": "Optional overall review summary",
            },
        },
    }

    result = []
    for t in get_all_tasks():
        result.append(
            {
                "id": t["id"],
                "name": t["name"],
                "description": t["description"],
                "difficulty": t["difficulty"],
                "max_steps": t["max_steps"],
                "pr_title": t["pr_title"],
                "file_name": t["file_name"],
                "action_schema": action_schema,
            }
        )
    return {"tasks": result, "action_schema": action_schema}


@app.post("/grader", response_model=GraderOutput, tags=["OpenEnv"])
def grader(grader_input: GraderInput):
    """
    Score a completed episode. Returns deterministic score between 0.0-1.0.
    Accepts episode history produced by /step calls.
    """
    try:
        result = grade_episode(grader_input)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# FIX 3: calls inference.py (renamed from baseline.py)
@app.post("/baseline", response_model=BaselineResponse, tags=["OpenEnv"])
def baseline():
    """
    Trigger the baseline inference script.
    Runs the agent against all 3 tasks and returns reproducible scores.
    Note: requires GEMINI_API_KEY environment variable.
    """
    try:
        import subprocess
        import json
        import sys

        result = subprocess.run(
            [sys.executable, "inference.py", "--output-json"],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Baseline script failed: {result.stderr}",
            )

        scores_data = json.loads(result.stdout)
        return BaselineResponse(
            scores=scores_data["scores"],
            model_used=scores_data.get("model_used", "gemini-2.0-flash"),
            note=scores_data.get("note", ""),
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Baseline script timed out")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse baseline output: {e}")


# ── Dashboard UI ─────────────────────────────────────────────────────────

@app.get("/dashboard", response_class=HTMLResponse, tags=["UI"])
def dashboard():
    """Serve the web dashboard UI"""
    html_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


# ── Entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=7860, reload=False)
