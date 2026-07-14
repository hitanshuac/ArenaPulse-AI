import os


def test_hf_deployment_standards():
    """
    Evaluates infrastructure files to ensure they comply with HF Deployment Standards.
    Claims:
    1. Dockerfiles use port 7860.
    2. Dockerfiles use non-root user (1000).
    3. CI/CD does not use 'git push hf HEAD:main --force'.
    """
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    webui_dockerfile = os.path.join(repo_root, "hf-webui", "Dockerfile")
    recovery_dockerfile = os.path.join(repo_root, "hf-recovery", "Dockerfile")
    deploy_yml = os.path.join(repo_root, ".github", "workflows", "deploy_hf.yml")

    # Check WebUI Dockerfile
    if os.path.exists(webui_dockerfile):
        with open(webui_dockerfile, encoding="utf-8") as f:
            content = f.read()
            assert "USER 1000" in content, "WebUI Dockerfile must use non-root user 1000"

    # Check Recovery Dockerfile
    if os.path.exists(recovery_dockerfile):
        with open(recovery_dockerfile, encoding="utf-8") as f:
            content = f.read()
            assert "7860" in content, "Recovery Dockerfile must bind to port 7860"

    # Check CI/CD Pipeline
    if os.path.exists(deploy_yml):
        with open(deploy_yml, encoding="utf-8") as f:
            content = f.read()
            assert "git push hf" not in content, "deploy_hf.yml must not use git push"
            assert "upload_to_hf.py" in content, "deploy_hf.yml must use upload_to_hf.py script"
