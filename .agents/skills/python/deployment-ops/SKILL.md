---
name: Deployment Operations
description: Technical implementation of Hugging Face Spaces deployments and Upstream syncing.
---

# Hugging Face Spaces Deployment Standards

## 1. Network & Container Constraints
* **Port Binding:** The application server must bind to `0.0.0.0:7860`.
* **Privilege Level:** The Docker container must run as a non-root user (uid `1000`).
* **Workers:** Run the ASGI server with a single worker (`--workers 1`).

## 2. Dependency Locking
* **Pin All Dependencies:** Always use pinned or range-locked versions in `requirements.txt`.
* **Known Conflict:** If using `python-telegram-bot`, it strictly requires `httpx~=0.26.0`.

## 3. Deployment Mechanism (CI/CD ONLY)
* **Use the SDK:** Always deploy using the custom `upload_to_hf.py` script via the Hugging Face Hub SDK.
* **CRITICAL:** `upload_to_hf.py` must ONLY be executed by the `.github/workflows/deploy_hf.yml` GitHub Action runner.

## 4. UI Integration
* **Single Endpoint:** Serve all interfaces (dashboard, chat console) on `/` via a unified, tabbed interface.

# Sync Upstream Workflow

## 1. Identify Hardened Rules via Git
* Run `git diff --name-status origin/main...HEAD .agents/` to find modified `.agents/` files.

## 2. Generate the Handover Template
* Overwrite `docs/handover-template.md` with the file paths and summary of changes.

## 3. Human-in-the-Loop Sync
* Inform the user that `docs/handover-template.md` is ready for manual copy-pasting.
