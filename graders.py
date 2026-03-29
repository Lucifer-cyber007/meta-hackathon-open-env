"""
Graders for each task. Each grader accepts episode history and returns
a deterministic float score between 0.0 and 1.0.
"""

from typing import List, Dict, Any
from reward import match_comments_to_issues
from tasks import get_task
from models import GraderInput, GraderOutput


def _extract_all_comments(episode_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Collect all comments the agent made across all steps in the episode."""
    all_comments = []
    for step in episode_history:
        action = step.get("action", {})
        comments = action.get("comments", [])
        all_comments.extend(comments)
    return all_comments


def _get_final_verdict(episode_history: List[Dict[str, Any]]) -> str:
    """Get the last verdict the agent issued."""
    for step in reversed(episode_history):
        verdict = step.get("action", {}).get("verdict")
        if verdict:
            return verdict
    return "comment"


def grade_episode(grader_input: GraderInput) -> GraderOutput:
    """
    Master grader — routes to the correct task grader and returns
    a deterministic, reproducible score between 0.0 and 1.0.
    """
    task = get_task(grader_input.task_id)
    if not task:
        return GraderOutput(
            score=0.0,
            task_id=grader_input.task_id,
            breakdown={"error": 0.0},
            feedback="Unknown task ID",
            issues_found=0,
            issues_missed=0,
            false_positives=0,
        )

    known_issues: List[Dict[str, Any]] = task["known_issues"]
    required_verdict: str = task["required_verdict"]
    history = grader_input.episode_history

    all_comments = _extract_all_comments(history)
    final_verdict = _get_final_verdict(history)

    issues_found, issues_missed, false_positives = match_comments_to_issues(
        all_comments, known_issues
    )

    total_issues = len(known_issues)
    breakdown: Dict[str, float] = {}
    feedback_parts: List[str] = []

    # ── 1. Detection rate (60% of score) ──────────────────────────────────
    detection_rate = issues_found / total_issues if total_issues > 0 else 0.0
    detection_score = round(detection_rate * 0.60, 4)
    breakdown["detection_score"] = detection_score
    feedback_parts.append(
        f"Detected {issues_found}/{total_issues} issues (detection_score={detection_score:.3f})"
    )

    # ── 2. Precision penalty — false positives (max -0.20) ────────────────
    precision_penalty = min(0.20, false_positives * 0.05)
    breakdown["precision_penalty"] = round(-precision_penalty, 4)
    if false_positives > 0:
        feedback_parts.append(
            f"{false_positives} false positive(s) (penalty={-precision_penalty:.3f})"
        )

    # ── 3. Verdict correctness (15% of score) ─────────────────────────────
    if final_verdict == required_verdict:
        verdict_score = 0.15
        feedback_parts.append(f"Correct verdict '{final_verdict}' (+0.15)")
    else:
        verdict_score = 0.0
        feedback_parts.append(
            f"Wrong verdict '{final_verdict}', expected '{required_verdict}' (+0.00)"
        )
    breakdown["verdict_score"] = verdict_score

    # ── 4. Severity weighting bonus (up to 0.15) ──────────────────────────
    severity_map = {"critical": 3, "major": 2, "minor": 1}
    total_severity_weight = sum(
        severity_map.get(i["severity"], 1) for i in known_issues
    )
    found_severity_weight = 0.0
    matched = set()
    for comment in all_comments:
        for idx, issue in enumerate(known_issues):
            if idx in matched:
                continue
            from reward import _line_proximity, _keywords_match
            if _line_proximity(comment.get("line_number", 0), issue["line_number"]) and \
               _keywords_match(comment.get("description", ""), issue["keywords"]):
                found_severity_weight += severity_map.get(issue["severity"], 1)
                matched.add(idx)
                break

    severity_score = 0.0
    if total_severity_weight > 0:
        severity_score = round(
            (found_severity_weight / total_severity_weight) * 0.15, 4
        )
    breakdown["severity_weighted_score"] = severity_score
    if severity_score > 0:
        feedback_parts.append(f"Severity-weighted coverage: +{severity_score:.3f}")

    # ── 5. Efficiency bonus — fewer steps = small bonus (up to 0.10) ──────
    steps_used = len(history)
    max_steps = task.get("max_steps", 5)
    if steps_used <= max(1, max_steps // 2):
        efficiency_bonus = 0.10
    elif steps_used <= max_steps:
        efficiency_bonus = 0.05
    else:
        efficiency_bonus = 0.0
    breakdown["efficiency_bonus"] = efficiency_bonus

    # ── Final score ────────────────────────────────────────────────────────
    raw_score = (
        detection_score
        - precision_penalty
        + verdict_score
        + severity_score
        + efficiency_bonus
    )
    final_score = round(max(0.0, min(1.0, raw_score)), 4)

    return GraderOutput(
        score=final_score,
        task_id=grader_input.task_id,
        breakdown=breakdown,
        feedback=" | ".join(feedback_parts),
        issues_found=issues_found,
        issues_missed=issues_missed,
        false_positives=false_positives,
    )
