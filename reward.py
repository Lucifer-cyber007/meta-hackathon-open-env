from typing import List, Dict, Any, Tuple
from models import Action, Reward


SEVERITY_SCORES = {
    "critical": 0.20,
    "major": 0.12,
    "minor": 0.05,
}

FALSE_POSITIVE_PENALTY = -0.08
WRONG_VERDICT_PENALTY = -0.15
CORRECT_VERDICT_BONUS = 0.10
STEP_PENALTY = -0.02  # small penalty per step to encourage efficiency


def _keywords_match(comment_text: str, known_keywords: List[str]) -> bool:
    """Check if a comment description contains enough keywords to match a known issue."""
    text_lower = comment_text.lower()
    matches = sum(1 for kw in known_keywords if kw.lower() in text_lower)
    return matches >= 1


def _line_proximity(comment_line: int, known_line: int, tolerance: int = 4) -> bool:
    """Allow line number matching within a tolerance window."""
    return abs(comment_line - known_line) <= tolerance


def match_comments_to_issues(
    comments: List[Dict[str, Any]],
    known_issues: List[Dict[str, Any]],
) -> Tuple[int, int, int]:
    """
    Match agent comments against known issues.
    Returns: (issues_found, issues_missed, false_positives)
    """
    matched_issues = set()
    false_positives = 0

    for comment in comments:
        comment_matched = False
        for idx, issue in enumerate(known_issues):
            if idx in matched_issues:
                continue
            line_ok = _line_proximity(
                comment.get("line_number", 0), issue["line_number"]
            )
            keyword_ok = _keywords_match(
                comment.get("description", ""), issue["keywords"]
            )
            if line_ok and keyword_ok:
                matched_issues.add(idx)
                comment_matched = True
                break

        if not comment_matched:
            false_positives += 1

    issues_found = len(matched_issues)
    issues_missed = len(known_issues) - issues_found
    return issues_found, issues_missed, false_positives


def calculate_reward(
    action: Action,
    known_issues: List[Dict[str, Any]],
    required_verdict: str,
    step_number: int,
) -> Reward:
    """
    Calculate reward with full trajectory signal (not just binary end-of-episode).
    Rewards partial progress and penalizes undesirable behaviour.
    """
    comments_data = [c.model_dump() for c in action.comments]
    issues_found, issues_missed, false_positives = match_comments_to_issues(
        comments_data, known_issues
    )

    breakdown: Dict[str, float] = {}

    # --- Positive: reward for each correctly identified issue ---
    # Weight by severity of the issues found
    issue_reward = 0.0
    matched_issues = set()
    for comment in comments_data:
        for idx, issue in enumerate(known_issues):
            if idx in matched_issues:
                continue
            if _line_proximity(comment.get("line_number", 0), issue["line_number"]) and \
               _keywords_match(comment.get("description", ""), issue["keywords"]):
                severity_bonus = SEVERITY_SCORES.get(issue["severity"], 0.05)
                issue_reward += severity_bonus
                matched_issues.add(idx)
                break

    breakdown["issue_detection"] = round(issue_reward, 4)

    # --- Negative: penalty for false positives ---
    fp_penalty = false_positives * FALSE_POSITIVE_PENALTY
    breakdown["false_positive_penalty"] = round(fp_penalty, 4)

    # --- Verdict correctness ---
    if action.verdict == required_verdict:
        breakdown["correct_verdict"] = CORRECT_VERDICT_BONUS
    else:
        breakdown["wrong_verdict"] = WRONG_VERDICT_PENALTY

    # --- Small step efficiency penalty ---
    step_pen = step_number * STEP_PENALTY
    breakdown["step_penalty"] = round(step_pen, 4)

    total = sum(breakdown.values())
    total = round(max(-1.0, min(1.0, total)), 4)

    message_parts = []
    if issues_found > 0:
        message_parts.append(f"Found {issues_found}/{len(known_issues)} known issues (+{issue_reward:.2f})")
    if issues_missed > 0:
        message_parts.append(f"Missed {issues_missed} issue(s)")
    if false_positives > 0:
        message_parts.append(f"{false_positives} false positive(s) ({fp_penalty:.2f})")
    if action.verdict == required_verdict:
        message_parts.append(f"Correct verdict '{action.verdict}' (+{CORRECT_VERDICT_BONUS})")
    else:
        message_parts.append(
            f"Wrong verdict '{action.verdict}' (expected '{required_verdict}') ({WRONG_VERDICT_PENALTY})"
        )

    return Reward(
        value=total,
        breakdown=breakdown,
        message=" | ".join(message_parts) if message_parts else "No reward signal",
        issues_found=issues_found,
        issues_missed=issues_missed,
        false_positives=false_positives,
    )
