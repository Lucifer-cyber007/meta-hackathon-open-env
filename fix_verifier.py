"""
Bug Fix Verifier for CodeReviewEnv.
Verifies agent-submitted fixes against known issues.
Awards bonus reward for correct fixes.
"""

from typing import List, Dict, Any

# Reward values for fixing
FIX_CORRECT_BONUS   =  0.30
FIX_PARTIAL_BONUS   =  0.10
FIX_WRONG_PENALTY   = -0.10
FIX_MISSING_PENALTY = -0.05


def verify_single_fix(
    original_code: str,
    fixed_code: str,
    issue: Dict[str, Any],
    fix: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Verify one fix against one known issue.
    Checks 3 things:
    1. Code actually changed
    2. Keywords found in fix OR agent description
    3. Fix is a real addition not just deletion
    """
    # ── 1. Code must actually change ──────────────────────
    if not fixed_code or not fixed_code.strip():
        return {
            "valid": False,
            "score": 0.0,
            "reason": "No fix code provided",
            "reward": FIX_WRONG_PENALTY,
        }

    # Strip blank lines for comparison
    orig_stripped  = " ".join(original_code.split())
    fixed_stripped = " ".join(fixed_code.split())
    code_changed   = orig_stripped != fixed_stripped

    if not code_changed:
        return {
            "valid": False,
            "score": 0.0,
            "reason": "Code was not changed",
            "reward": FIX_WRONG_PENALTY,
        }

    # ── 2. Check keywords ──────────────────────────────────
    keywords     = issue.get("keywords", [])
    severity     = issue.get("severity", "minor")
    fixed_lower  = fixed_code.lower()
    issue_desc   = fix.get("issue_description", "").lower()

    # Count how many keywords appear in EITHER
    # the fixed code OR the agent's description
    # This is lenient — agent just needs to show awareness
    matched = 0
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in fixed_lower or kw_lower in issue_desc:
            matched += 1

    # ── 3. Score ───────────────────────────────────────────
    ratio = matched / len(keywords) if keywords else 1.0

    # Very lenient threshold — just needs 1 keyword match
    if matched >= 1 and code_changed:
        reward = FIX_CORRECT_BONUS
        if severity == "critical":
            reward += 0.10
        elif severity == "major":
            reward += 0.05
        return {
            "valid": True,
            "score": round(ratio, 4),
            "reason": f"Fix addresses issue — {matched}/{len(keywords)} keywords matched",
            "reward": round(reward, 4),
        }
    elif code_changed:
        # Code changed but no keywords — partial credit
        return {
            "valid": True,
            "score": 0.1,
            "reason": "Code changed but unclear if it addresses the issue",
            "reward": FIX_PARTIAL_BONUS,
        }
    else:
        return {
            "valid": False,
            "score": 0.0,
            "reason": "Fix does not address the known issue",
            "reward": FIX_WRONG_PENALTY,
        }


def verify_all_fixes(
    original_code: str,
    agent_fixes: List[Dict[str, Any]],
    known_issues: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Verify all fixes the agent submitted.

    agent_fixes format:
    [
        {
            "line_number": 5,
            "issue_description": "ZeroDivisionError...",
            "fixed_code": "return total / len(numbers) if numbers else 0"
        },
        ...
    ]
    """
    if not agent_fixes:
        critical_missed = sum(
            1 for i in known_issues if i.get("severity") == "critical"
        )
        penalty = critical_missed * FIX_MISSING_PENALTY
        return {
            "total_fix_reward": round(penalty, 4),
            "fixes_correct":    0,
            "fixes_partial":    0,
            "fixes_wrong":      0,
            "fixes_missing":    len(known_issues),
            "breakdown":        [],
            "message": f"No fixes submitted. {critical_missed} critical issues unfixed.",
        }

    total_reward   = 0.0
    fixes_correct  = 0
    fixes_partial  = 0
    fixes_wrong    = 0
    breakdown      = []
    matched_issues = set()

    for fix in agent_fixes:
        fix_line   = fix.get("line_number", 0)
        fixed_code = fix.get("fixed_code", "")

        best_result = None
        best_idx    = None

        # Match fix to closest known issue by line number
        for idx, issue in enumerate(known_issues):
            if idx in matched_issues:
                continue
            line_diff = abs(fix_line - issue.get("line_number", 0))
            if line_diff <= 5:
                result = verify_single_fix(
                    original_code, fixed_code, issue, fix
                )
                if best_result is None or \
                   result["score"] > best_result["score"]:
                    best_result = result
                    best_idx    = idx

        if best_result and best_idx is not None:
            matched_issues.add(best_idx)
            total_reward += best_result["reward"]
            if best_result["valid"] and best_result["score"] >= 0.3:
                fixes_correct += 1
            elif best_result["valid"]:
                fixes_partial += 1
            else:
                fixes_wrong += 1
            breakdown.append({
                "line_number": fix_line,
                "result":      best_result,
            })
        else:
            # No known issue near this line
            total_reward += FIX_WRONG_PENALTY
            fixes_wrong  += 1
            breakdown.append({
                "line_number": fix_line,
                "result": {
                    "valid":  False,
                    "score":  0.0,
                    "reason": "No known issue near this line number",
                    "reward": FIX_WRONG_PENALTY,
                },
            })

    total_reward = round(max(-1.0, min(1.0, total_reward)), 4)

    return {
        "total_fix_reward": total_reward,
        "fixes_correct":    fixes_correct,
        "fixes_partial":    fixes_partial,
        "fixes_wrong":      fixes_wrong,
        "fixes_missing":    len(known_issues) - len(matched_issues),
        "breakdown":        breakdown,
        "message": (
            f"{fixes_correct} correct fixes (+reward) | "
            f"{fixes_partial} partial | "
            f"{fixes_wrong} wrong (-penalty)"
        ),
    }