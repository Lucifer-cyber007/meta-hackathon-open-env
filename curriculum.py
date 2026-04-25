"""
Curriculum Learning for CodeReviewEnv.
Tracks agent scores and promotes to harder tasks
when performance threshold is met.
"""

from typing import Dict, List

CURRICULUM_MAP = {
    "easy":           {"next": "medium",        "threshold": 0.75},
    "medium":         {"next": "hard",          "threshold": 0.70},
    "js-async":       {"next": "js_async",      "threshold": 0.65},
    "js_async":       {"next": "api_security",  "threshold": 0.65},
    "sql-injection":  {"next": "orm_bugs",      "threshold": 0.65},
    "orm_bugs":       {"next": "data_pipeline", "threshold": 0.65},
    "react-security": {"next": "auth_system",   "threshold": 0.65},
    "api_security":   {"next": "auth_system",   "threshold": 0.60},
    "auth_system":    {"next": "hard",          "threshold": 0.60},
    "data_pipeline":  {"next": "hard",          "threshold": 0.60},
    "django-auth":    {"next": "hard",          "threshold": 0.60},
    "node-race":      {"next": "hard",          "threshold": 0.55},
}

WINDOW_SIZE = 3


class CurriculumTracker:
    def __init__(self):
        self.scores_history: Dict[str, List[float]] = {}
        self.promotions: List[Dict] = []

    def update(self, task_id: str, score: float) -> dict:
        if task_id not in self.scores_history:
            self.scores_history[task_id] = []

        self.scores_history[task_id].append(round(score, 4))
        self.scores_history[task_id] = \
            self.scores_history[task_id][-WINDOW_SIZE:]

        recent = self.scores_history[task_id]
        avg = round(sum(recent) / len(recent), 4)
        promoted = False
        next_task = task_id

        if task_id in CURRICULUM_MAP:
            cfg = CURRICULUM_MAP[task_id]
            if len(recent) >= WINDOW_SIZE and avg >= cfg["threshold"]:
                next_task = cfg["next"]
                promoted = True
                self.promotions.append({
                    "from_task": task_id,
                    "to_task": next_task,
                    "avg_score": avg,
                    "threshold": cfg["threshold"],
                })

        return {
            "current_task": task_id,
            "recommended_next": next_task,
            "promoted": promoted,
            "recent_scores": recent,
            "average_score": avg,
            "episodes_on_task": len(self.scores_history[task_id]),
        }

    def get_state(self) -> dict:
        progress = {}
        for task_id, scores in self.scores_history.items():
            avg = round(sum(scores) / len(scores), 4) if scores else 0.0
            cfg = CURRICULUM_MAP.get(task_id, {})
            progress[task_id] = {
                "recent_scores": scores,
                "average": avg,
                "threshold": cfg.get("threshold", None),
                "next_task": cfg.get("next", None),
                "mastered": avg >= cfg.get("threshold", 1.0)
                            and len(scores) >= WINDOW_SIZE,
            }
        return {
            "progress": progress,
            "promotions_log": self.promotions,
            "total_promotions": len(self.promotions),
            "curriculum_map": CURRICULUM_MAP,
        }

    def reset(self):
        self.scores_history = {}
        self.promotions = []


curriculum_tracker = CurriculumTracker()
