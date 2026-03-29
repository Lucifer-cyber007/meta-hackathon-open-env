from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any


class CodeComment(BaseModel):
    line_number: int = Field(..., description="Line number being commented on (1-indexed)")
    issue_type: Literal["bug", "security", "performance", "style", "logic"] = Field(
        ..., description="Type of issue found"
    )
    severity: Literal["critical", "major", "minor"] = Field(
        ..., description="Severity level of the issue"
    )
    description: str = Field(..., description="Detailed description of the issue found")
    suggested_fix: Optional[str] = Field(None, description="Suggested fix for the issue")


class Action(BaseModel):
    comments: List[CodeComment] = Field(
        default_factory=list, description="List of code review comments on specific lines"
    )
    verdict: Literal["approve", "request_changes", "comment"] = Field(
        ..., description="Final verdict on the pull request"
    )
    summary: Optional[str] = Field(None, description="Overall summary of the review")


class Observation(BaseModel):
    diff: str = Field(..., description="The code diff/patch to review")
    file_name: str = Field(..., description="Name of the file being reviewed")
    pr_title: str = Field(..., description="Title of the pull request")
    pr_description: str = Field(..., description="Description of the pull request")
    step_number: int = Field(..., description="Current step number in the episode")
    max_steps: int = Field(..., description="Maximum steps allowed in this episode")
    task_id: str = Field(..., description="Current task identifier (easy/medium/hard)")
    task_description: str = Field(..., description="Description of the task objective")


class Reward(BaseModel):
    value: float = Field(..., description="Reward value between -1.0 and 1.0")
    breakdown: Dict[str, float] = Field(
        default_factory=dict, description="Breakdown of reward components"
    )
    message: str = Field(..., description="Human-readable explanation of the reward")
    issues_found: int = Field(0, description="Number of issues correctly identified")
    issues_missed: int = Field(0, description="Number of known issues missed")
    false_positives: int = Field(0, description="Number of false positive comments")


class EnvironmentState(BaseModel):
    task_id: str
    step_number: int
    max_steps: int
    done: bool
    total_reward: float
    current_diff: str
    known_issue_count: int
    agent_comment_count: int
    episode_history: List[Dict[str, Any]]


class TaskInfo(BaseModel):
    id: str
    name: str
    description: str
    difficulty: Literal["easy", "medium", "hard"]
    max_steps: int
    action_schema: Dict[str, Any]


class GraderInput(BaseModel):
    task_id: str
    episode_history: List[Dict[str, Any]]
    final_action: Optional[Dict[str, Any]] = None


class GraderOutput(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0, description="Score between 0.0 and 1.0")
    task_id: str
    breakdown: Dict[str, float]
    feedback: str
    issues_found: int
    issues_missed: int
    false_positives: int
