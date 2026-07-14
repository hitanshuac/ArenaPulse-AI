---
name: agent-evals
description: "Instructs the agent to build evaluation harnesses for LLM agents using trajectory scoring, tool-call accuracy metrics, and LLM-as-judge rubrics. Encodes the two-layer approach (offline CI/CD + online per-turn monitoring) from 2026 industry standards. TRIGGERS: 'evaluate agent performance', 'build agent evals', 'agent evaluation harness', 'trajectory scoring', 'tool-call accuracy', 'LLM as judge', 'agent benchmarking', 'test agent quality'."
---

# Agent Evals Skill

This skill instructs the IDE copilot to build production-grade evaluation harnesses for LLM agents. In 2026, evaluating agents has shifted from simple input-output matching to **trajectory-based evaluation** — assessing the entire reasoning chain, not just the final answer.

> **Key Insight:** A correct final answer can result from a dangerous path (infinite loops, redundant tool calls, unauthorized actions). Evaluating only the output misses 80% of production failure modes.

---

## Anti-Patterns (MUST Avoid)

### 1. Output-Only Evaluation
- **What it is:** Testing only whether the final answer is correct, ignoring the reasoning path.
- **Rule:** ALWAYS evaluate the full trajectory: thoughts → tool calls → intermediate results → final answer.

### 2. No Regression Suite
- **What it is:** Running evals manually and never capturing failures as test cases.
- **Rule:** Every production failure MUST be captured as a regression test. The trace becomes a test fixture. The expected behavior becomes the assertion.

### 3. Uncalibrated LLM Judges
- **What it is:** Using an LLM to evaluate another LLM's output without structured rubrics or calibration against human labels.
- **Rule:** LLM-as-judge evaluations MUST use structured rubrics with explicit scoring criteria. Calibrate against at least 20 human-labeled examples before trusting judge scores.

### 4. Missing Cost Tracking
- **What it is:** Evaluating quality without tracking token consumption, API costs, or step efficiency.
- **Rule:** Every eval run MUST report: total tokens consumed, total API calls, total steps taken, and cost estimate.

---

## Scaffolding Instructions

When the user asks to build an agent evaluation harness, follow this exact sequence:

### Step 1: Define the Metric Categories
```python
from dataclasses import dataclass
from enum import Enum

class MetricType(Enum):
    DETERMINISTIC = "deterministic"  # Exact checks, no LLM needed
    JUDGE_BASED = "judge_based"      # Requires LLM-as-judge

@dataclass
class EvalMetric:
    name: str
    type: MetricType
    description: str
    weight: float  # 0.0 to 1.0, weights MUST sum to 1.0

# Core metrics every agent eval MUST include:
REQUIRED_METRICS = [
    EvalMetric("tool_call_accuracy", MetricType.DETERMINISTIC,
               "Did the agent call the correct tool with valid arguments?", 0.25),
    EvalMetric("plan_adherence", MetricType.JUDGE_BASED,
               "Did the agent follow an efficient strategy?", 0.20),
    EvalMetric("step_efficiency", MetricType.DETERMINISTIC,
               "Did the agent avoid unnecessary steps and redundant loops?", 0.15),
    EvalMetric("task_completion", MetricType.JUDGE_BASED,
               "Did the agent successfully complete the assigned task?", 0.25),
    EvalMetric("safety_compliance", MetricType.DETERMINISTIC,
               "No PII leaks, unauthorized actions, or policy violations?", 0.15),
]
```

### Step 2: Build the Trajectory Recorder
```python
from datetime import datetime
from pydantic import BaseModel

class TrajectoryStep(BaseModel):
    timestamp: datetime
    step_type: str  # "thought", "tool_call", "tool_result", "final_answer"
    content: str
    tool_name: str | None = None
    tool_args: dict | None = None
    tokens_used: int = 0

class AgentTrajectory(BaseModel):
    task: str
    steps: list[TrajectoryStep]
    final_answer: str
    total_tokens: int
    total_steps: int
    total_tool_calls: int
    duration_seconds: float

def record_trajectory(agent, task: str) -> AgentTrajectory:
    """Execute an agent and capture its full trajectory."""
    steps = []
    start = datetime.utcnow()
    # ... instrument agent execution to capture each step
    return AgentTrajectory(
        task=task,
        steps=steps,
        final_answer=final,
        total_tokens=sum(s.tokens_used for s in steps),
        total_steps=len(steps),
        total_tool_calls=len([s for s in steps if s.step_type == "tool_call"]),
        duration_seconds=(datetime.utcnow() - start).total_seconds(),
    )
```

### Step 3: Implement Deterministic Metrics
```python
def eval_tool_call_accuracy(
    trajectory: AgentTrajectory,
    expected_tools: list[str],
) -> float:
    """Check if the agent called the correct tools."""
    actual_tools = [
        s.tool_name for s in trajectory.steps if s.step_type == "tool_call"
    ]
    if not expected_tools:
        return 1.0 if not actual_tools else 0.0

    correct = sum(1 for t in actual_tools if t in expected_tools)
    return correct / max(len(expected_tools), len(actual_tools))

def eval_step_efficiency(
    trajectory: AgentTrajectory,
    max_expected_steps: int,
) -> float:
    """Penalize excessive steps. Score 1.0 if within budget, degrades linearly."""
    if trajectory.total_steps <= max_expected_steps:
        return 1.0
    overshoot = trajectory.total_steps - max_expected_steps
    return max(0.0, 1.0 - (overshoot / max_expected_steps))

def eval_safety_compliance(trajectory: AgentTrajectory) -> float:
    """Check for PII leaks and unauthorized actions."""
    import re
    pii_patterns = [
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
    ]
    for step in trajectory.steps:
        for pattern in pii_patterns:
            if re.search(pattern, step.content):
                return 0.0  # Immediate fail on PII leak
    return 1.0
```

### Step 4: Implement LLM-as-Judge Metrics
```python
JUDGE_RUBRIC = """
You are evaluating an AI agent's performance on a task.

## Task
{task}

## Agent Trajectory
{trajectory}

## Scoring Criteria
Rate the agent on a scale of 1-5 for each dimension:

1. **Plan Adherence** (1-5): Did the agent follow a logical, efficient strategy?
   - 5: Optimal path, no wasted steps
   - 3: Reasonable path with minor inefficiencies
   - 1: Chaotic, no clear strategy

2. **Task Completion** (1-5): Did the agent successfully complete the task?
   - 5: Fully completed with correct output
   - 3: Partially completed
   - 1: Failed or produced incorrect output

Return your evaluation as JSON:
{{"plan_adherence": <1-5>, "task_completion": <1-5>, "reasoning": "<explanation>"}}
"""

def eval_with_judge(trajectory: AgentTrajectory) -> dict:
    """Use LLM-as-judge with structured rubric."""
    prompt = JUDGE_RUBRIC.format(
        task=trajectory.task,
        trajectory=format_trajectory_for_judge(trajectory),
    )
    result = judge_model.with_structured_output(JudgeResponse).invoke(prompt)
    return {
        "plan_adherence": result.plan_adherence / 5.0,
        "task_completion": result.task_completion / 5.0,
    }
```

### Step 5: Build the Eval Runner (CI/CD Compatible)
```python
import json

def run_eval_suite(
    agent,
    test_cases: list[dict],
    output_path: str = "eval_results.json",
) -> dict:
    """Run a full evaluation suite. Compatible with pytest and CI/CD."""
    results = []
    for case in test_cases:
        trajectory = record_trajectory(agent, case["task"])

        # Deterministic metrics
        tool_accuracy = eval_tool_call_accuracy(trajectory, case.get("expected_tools", []))
        step_efficiency = eval_step_efficiency(trajectory, case.get("max_steps", 10))
        safety = eval_safety_compliance(trajectory)

        # Judge-based metrics
        judge_scores = eval_with_judge(trajectory)

        score = (
            0.25 * tool_accuracy +
            0.20 * judge_scores["plan_adherence"] +
            0.15 * step_efficiency +
            0.25 * judge_scores["task_completion"] +
            0.15 * safety
        )

        results.append({
            "task": case["task"],
            "overall_score": round(score, 3),
            "tool_accuracy": tool_accuracy,
            "plan_adherence": judge_scores["plan_adherence"],
            "step_efficiency": step_efficiency,
            "task_completion": judge_scores["task_completion"],
            "safety": safety,
            "total_tokens": trajectory.total_tokens,
            "total_steps": trajectory.total_steps,
        })

    summary = {
        "total_cases": len(results),
        "avg_score": round(sum(r["overall_score"] for r in results) / len(results), 3),
        "pass_rate": sum(1 for r in results if r["overall_score"] >= 0.7) / len(results),
        "results": results,
    }

    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)

    return summary
```

### Step 6: Regression Test Template
```python
# tests/test_agent_regression.py
import pytest
import json

def load_regression_cases():
    with open("tests/fixtures/agent_regression_cases.json") as f:
        return json.load(f)

@pytest.mark.parametrize("case", load_regression_cases())
def test_agent_regression(agent, case):
    """Regression test: ensure previously fixed failures stay fixed."""
    trajectory = record_trajectory(agent, case["task"])
    score = eval_tool_call_accuracy(trajectory, case["expected_tools"])
    assert score >= case["min_score"], (
        f"Regression detected: {case['task']} scored {score}, "
        f"expected >= {case['min_score']}"
    )
```

---

## Two-Layer Evaluation Strategy

| Layer | When | What | Tool |
|:---|:---|:---|:---|
| **Offline (CI/CD)** | Before deployment | Full trajectory suite, regression tests | pytest + eval runner |
| **Online (Per-Turn)** | During inference | Lightweight safety checks, step caps | Inline monitors |

---

## Required Dependencies
```
pydantic>=2.0
pytest>=8.0
```

## Reference Implementations
- `Marker-Inc-Korea/AutoRAG` — RAG evaluation with AutoML-style optimization (4,853★)
- LangSmith — Trajectory-native evaluation and observability
- DeepEval — CI/CD-compatible, pytest-style agent metrics
