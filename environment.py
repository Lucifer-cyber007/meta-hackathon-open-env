"""
CodeReviewEnv — OpenEnv-compliant environment for AI agent code review training.

Implements: step() / reset() / state()
"""

from typing import Any, Dict, Optional, Tuple
from models import Action, Observation, Reward, EnvironmentState
from tasks import get_task, get_all_tasks
from reward import calculate_reward


class CodeReviewEnv:
    """
    An OpenEnv environment that simulates a human code reviewer's workflow.

    The agent receives a code diff and must identify bugs, security issues,
    and style problems by submitting CodeComment actions with severity ratings.
    At the end of each episode the agent issues a final verdict.
    """

    def __init__(self, task_id: str = "easy"):
        self.task_id = task_id
        self._task: Dict[str, Any] = {}
        self._step_number: int = 0
        self._done: bool = False
        self._total_reward: float = 0.0
        self._episode_history: list = []
        self._current_observation: Optional[Observation] = None

    # ──────────────────────────────────────────────────────────────────────
    # OpenEnv Core API
    # ──────────────────────────────────────────────────────────────────────

    def reset(self, task_id: Optional[str] = None) -> Observation:
        """Reset the environment to a clean initial state. Returns first observation."""
        if task_id:
            self.task_id = task_id

        self._task = get_task(self.task_id)
        if not self._task:
            raise ValueError(f"Unknown task_id: '{self.task_id}'. "
                             f"Valid options: {[t['id'] for t in get_all_tasks()]}")

        self._step_number = 0
        self._done = False
        self._total_reward = 0.0
        self._episode_history = []

        self._current_observation = Observation(
            diff=self._task["diff"],
            file_name=self._task["file_name"],
            pr_title=self._task["pr_title"],
            pr_description=self._task["pr_description"],
            step_number=self._step_number,
            max_steps=self._task["max_steps"],
            task_id=self.task_id,
            task_description=self._task["description"],
        )
        return self._current_observation

    def step(self, action: Action) -> Tuple[Observation, float, bool, Dict[str, Any]]:
        """
        Process one agent action and return (observation, reward, done, info).

        Args:
            action: An Action object with comments and a verdict.

        Returns:
            observation: Updated observation (same diff, updated step counter).
            reward:      Float reward signal for this step.
            done:        True when episode is complete.
            info:        Dict with reward breakdown and debug info.
        """
        if self._done:
            raise RuntimeError(
                "Episode is finished. Call reset() to start a new episode."
            )
        if not self._task:
            raise RuntimeError("Environment not initialised. Call reset() first.")

        self._step_number += 1

        # Calculate reward for this action
        reward_obj: Reward = calculate_reward(
            action=action,
            known_issues=self._task["known_issues"],
            required_verdict=self._task["required_verdict"],
            step_number=self._step_number,
        )

        self._total_reward += reward_obj.value

        # Record step in history
        step_record = {
            "step": self._step_number,
            "action": action.model_dump(),
            "reward": reward_obj.value,
            "reward_breakdown": reward_obj.breakdown,
            "reward_message": reward_obj.message,
            "issues_found_this_step": reward_obj.issues_found,
            "false_positives_this_step": reward_obj.false_positives,
        }
        self._episode_history.append(step_record)

        # Determine if episode is done
        max_steps = self._task["max_steps"]
        verdict_issued = action.verdict in ("approve", "request_changes")
        self._done = verdict_issued or (self._step_number >= max_steps)

        # Build next observation
        self._current_observation = Observation(
            diff=self._task["diff"],
            file_name=self._task["file_name"],
            pr_title=self._task["pr_title"],
            pr_description=self._task["pr_description"],
            step_number=self._step_number,
            max_steps=max_steps,
            task_id=self.task_id,
            task_description=self._task["description"],
        )

        info = {
            "reward_breakdown": reward_obj.breakdown,
            "reward_message": reward_obj.message,
            "issues_found": reward_obj.issues_found,
            "issues_missed": reward_obj.issues_missed,
            "false_positives": reward_obj.false_positives,
            "total_reward_so_far": round(self._total_reward, 4),
            "steps_remaining": max(0, max_steps - self._step_number),
        }

        return self._current_observation, reward_obj.value, self._done, info

    def state(self) -> EnvironmentState:
        """Return the full current internal state of the environment."""
        return EnvironmentState(
            task_id=self.task_id,
            step_number=self._step_number,
            max_steps=self._task.get("max_steps", 0) if self._task else 0,
            done=self._done,
            total_reward=round(self._total_reward, 4),
            current_diff=self._task.get("diff", "") if self._task else "",
            known_issue_count=len(self._task.get("known_issues", [])) if self._task else 0,
            agent_comment_count=sum(
                len(s.get("action", {}).get("comments", []))
                for s in self._episode_history
            ),
            episode_history=self._episode_history,
        )
