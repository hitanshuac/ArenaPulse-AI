import logging
from collections.abc import Callable
from typing import Any

from arenapulse.rules import BaseRule, RuleResult

logger = logging.getLogger("arenapulse")


class ExecutionError(Exception):
    """Raised when an action fails deterministic rule validation."""
    pass


class ArenaEngine:
    """
    Zero-Hallucination Execution & State Guardrail Engine.

    Usage:
        engine = ArenaEngine()
        engine.add_rule(PathSafetyRule(allowed_roots=["./data"]))
        result = engine.verify_and_execute("write_file", {"target_file": "./data/output.txt"})
    """

    def __init__(self, name: str = "ArenaPulse-Instance"):
        self.name = name
        self.rules: list[BaseRule] = []

    def add_rule(self, rule: BaseRule) -> "ArenaEngine":
        """Registers a deterministic rule with the engine."""
        self.rules.append(rule)
        logger.info(f"Registered rule '{rule.name}' with ArenaEngine.")
        return self

    def verify(self, action_type: str, payload: Any) -> list[RuleResult]:
        """Evaluates all registered rules against the proposed action."""
        results = []
        for rule in self.rules:
            res = rule.evaluate(action_type, payload)
            results.append(res)
            if not res.allowed:
                logger.warning(f"Rule '{res.rule_name}' rejected action '{action_type}': {res.reason}")
        return results

    def verify_and_execute(
        self, action_type: str, payload: Any, executor: Callable[[Any], Any] | None = None
    ) -> Any:
        """
        Validates the action across all rules. If allowed, executes the optional callback.
        Throws ExecutionError if any rule rejects the action.
        """
        results = self.verify(action_type, payload)
        failures = [r for r in results if not r.allowed]

        if failures:
            reasons = "; ".join([f"{f.rule_name}: {f.reason}" for f in failures])
            raise ExecutionError(f"Action '{action_type}' blocked by zero-hallucination guardrails: {reasons}")

        logger.info(f"Action '{action_type}' successfully passed all {len(self.rules)} rule check(s).")
        if executor:
            return executor(payload)
        return {"status": "SUCCESS", "action_type": action_type, "payload": payload}
