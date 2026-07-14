---
trigger: glob
glob: "tests/**/*.py, *_test.py"
---

# SRE Standard Operating Procedure (SOP)

## 1. The "Inner Loop" (Continuous Iteration)
- **Trigger:** After EVERY code modification.
- **Action:** The agent MUST autonomously execute the `.agents/workflows/test-automation.md` workflow.
- **Enforcement:**
  1. Execute the host project's test suite.
  2. If tests fail, execute `.agents/workflows/error-observability.md` to log the failure, fix the code, and retry.
  3. If the agent fails to fix the test after 3 attempts, it MUST explicitly halt execution and ask the user for manual intervention.
  4. The Inner Loop is ONLY successful when the test runner returns exit code `0` AND at least 1 test passed.
  5. The agent MUST provide explicit UI/CLI commands to test the feature manually and wait for human approval.

## 2. The "Outer Loop" (Ticket Conclusion)
- **Trigger:** When all Acceptance Criteria for the current ticket are marked complete `[x]`, and the Inner Loop Success Condition is met.
- **Action:** The agent MUST autonomously execute the `.agents/workflows/master-sync.md` workflow.
- **Enforcement:** The agent MUST explicitly complete the Outer Loop (the `master-sync.md` commit) before beginning work on the next ticket.
