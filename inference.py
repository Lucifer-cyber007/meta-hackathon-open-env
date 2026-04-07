"""
Baseline inference script for CodeReviewEnv.

Uses Google Gemini API (FREE tier) via the OpenAI-compatible client.
Gemini free tier: 1500 requests/day on gemini-1.5-flash — no credit card needed.

Get your free API key at: https://aistudio.google.com/app/apikey

Usage:
    python inference.py
    python inference.py --output-json      # used by /baseline endpoint
    python inference.py --task easy        # single task only
"""

import os
import sys
import json
import argparse
from typing import Dict, Any

from openai import OpenAI
from environment import CodeReviewEnv
from graders import grade_episode
from models import Action, CodeComment, GraderInput


# ── Priority: use the hackathon proxy vars first ──────────────────
API_KEY = os.environ.get("API_KEY") or os.environ.get("GEMINI_API_KEY", "")
API_BASE_URL = os.environ.get("API_BASE_URL") or "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_MODEL = os.environ.get("MODEL", "gpt-4o-mini")

# Debug: log which endpoint we're hitting (visible in validator logs)
print(f"[CONFIG] API_BASE_URL={API_BASE_URL}", flush=True)
print(f"[CONFIG] MODEL={DEFAULT_MODEL}", flush=True)
print(f"[CONFIG] API_KEY set={'yes' if API_KEY else 'NO — MISSING!'}", flush=True)


SYSTEM_PROMPT = """You are an expert code reviewer. You will be given a code diff from a pull request.
Your job is to identify ALL bugs, security vulnerabilities, performance issues, and logic errors.

For each issue you find, specify:
- line_number: integer line number in the diff
- issue_type: one of "bug", "security", "performance", "style", "logic"
- severity: one of "critical", "major", "minor"
- description: clear explanation
- suggested_fix: optional fix

Respond with ONLY valid JSON, no markdown, no extra text:
{
  "comments": [
    {
      "line_number": <int>,
      "issue_type": "<type>",
      "severity": "<severity>",
      "description": "<description>",
      "suggested_fix": "<optional>"
    }
  ],
  "verdict": "<approve|request_changes|comment>",
  "summary": "<brief summary>"
}

Look for: empty list crashes, SQL injection, hardcoded secrets, weak crypto (MD5),
race conditions, silent exceptions, dict mutation during iteration, logic errors."""


def build_user_prompt(obs: Dict[str, Any]) -> str:
    return f"""PR Title: {obs['pr_title']}
File: {obs['file_name']}
Task: {obs['task_description']}

Code Diff:
{obs['diff']}

Return ONLY a JSON object with your findings."""


def parse_llm_response(content: str) -> Action:
    clean = content.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        clean = "\n".join(lines[1:])
        if clean.strip().endswith("```"):
            clean = clean.strip()[:-3].strip()

    data = json.loads(clean)
    comments = []
    for c in data.get("comments", []):
        try:
            comments.append(CodeComment(
                line_number=int(c.get("line_number", 1)),
                issue_type=c.get("issue_type", "bug"),
                severity=c.get("severity", "minor"),
                description=str(c.get("description", "")),
                suggested_fix=c.get("suggested_fix"),
            ))
        except Exception:
            continue
    return Action(
        comments=comments,
        verdict=data.get("verdict", "comment"),
        summary=data.get("summary"),
    )


def run_task(client: OpenAI, task_id: str, model: str, verbose: bool = True) -> Dict[str, Any]:
    env = CodeReviewEnv(task_id=task_id)
    obs = env.reset(task_id=task_id)

    if verbose:
        print(f"\n{'='*60}\n  Task: {task_id.upper()} — {obs.file_name}\n{'='*60}", flush=True)

    # ── REQUIRED: Print [START] block ──────────────────────────
    print(f"[START] task={task_id}", flush=True)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(obs.model_dump())},
            ],
            temperature=0.0,
            max_tokens=2000,
        )
        action = parse_llm_response(response.choices[0].message.content)
    except Exception as e:
        if verbose:
            print(f"  [ERROR] {e}", flush=True)
        action = Action(comments=[], verdict="comment", summary=f"Error: {e}")

    _, reward, _, info = env.step(action)

    # ── REQUIRED: Print [STEP] block ───────────────────────────
    print(f"[STEP] step=1 reward={reward:.4f}", flush=True)

    episode_history = [{
        "step": 1,
        "action": action.model_dump(),
        "reward": reward,
        "reward_breakdown": info.get("reward_breakdown", {}),
        "reward_message": info.get("reward_message", ""),
        "issues_found_this_step": info.get("issues_found", 0),
        "false_positives_this_step": info.get("false_positives", 0),
    }]

    result = grade_episode(GraderInput(task_id=task_id, episode_history=episode_history))

    # ── REQUIRED: Print [END] block ────────────────────────────
    print(f"[END] task={task_id} score={result.score:.4f} steps=1", flush=True)

    if verbose:
        print(f"  Comments   : {len(action.comments)}", flush=True)
        print(f"  Verdict    : {action.verdict}", flush=True)
        print(f"  Score      : {result.score:.4f}", flush=True)
        print(f"  Feedback   : {result.feedback[:100]}", flush=True)

    return {
        "task_id": task_id,
        "task_name": env._task.get("name", task_id),
        "difficulty": env._task.get("difficulty", task_id),
        "score": result.score,
        "feedback": result.feedback,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--task", default=None)
    parser.add_argument("--output-json", action="store_true")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: No API_KEY or GEMINI_API_KEY env variable found.", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)
    task_ids = [args.task] if args.task else ["easy", "medium", "hard"]
    results = [run_task(client, t, args.model, not args.output_json) for t in task_ids]

    if args.output_json:
        print(json.dumps({
            "scores": [{"task_id": r["task_id"], "task_name": r["task_name"],
                        "difficulty": r["difficulty"], "score": r["score"],
                        "feedback": r["feedback"]} for r in results],
            "model_used": args.model,
            "note": "Temperature=0. Provider: Google Gemini free tier.",
        }), flush=True)
    else:
        print(f"\n{'='*60}\n  BASELINE SCORES\n{'='*60}", flush=True)
        for r in results:
            print(f"  {r['task_id']:8s} {r['score']:.4f}", flush=True)
        avg = sum(r['score'] for r in results) / len(results)
        print(f"  Average: {avg:.4f}", flush=True)


if __name__ == "__main__":
    main()