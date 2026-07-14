---
description: Automatically fetch, diagnose, and resolve remote CI/CD pipeline failures directly in the local terminal.
---

# CI/CD Error Synchronization Workflow

**Trigger:** Explicit invocation via `/ask run @[.agents/workflows/sync-ci-errors.md]` after receiving a GitHub Actions failure notification.

This workflow bridges the gap between remote cloud CI/CD pipelines and local agentic observability. It allows the AI to fetch remote failure logs without opening a browser and immediately begin diagnosing the code.

## Phase 1: Fetch Remote Logs
1. Use the GitHub CLI to find the most recent failed workflow run: // turbo
   - `gh run list --status failure --limit 1 --json databaseId,name,conclusion,createdAt`
2. Fetch the full failure logs for that run: // turbo
   - `gh run view <databaseId> --log-failed`
3. Parse the failure output and inject a structured error entry into `data/error_logs.json` following the canonical schema from `error-observability.md`.

## Phase 2: Local Diagnosis
1. Execute the Error Observability workflow to read the newly imported error:
2. Execute `.agents/workflows/error-observability.md`
3. Analyze the stack trace injected into `data/error_logs.json` tagged as `CI/CD Remote Failure`.

## Phase 3: Autonomous Resolution
1. Based on the logs, autonomously generate the code fixes locally.
2. Present the proposed fixes to the user using an `implementation_plan.md` artifact.
3. Wait for user approval before modifying code.

## Phase 4: Verification
1. Once the user approves and fixes are applied, trigger the Master Sync workflow to push the fixes back to the cloud:
2. Execute `.agents/workflows/master-sync.md`
