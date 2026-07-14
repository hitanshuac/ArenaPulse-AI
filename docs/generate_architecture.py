import os

from diagrams import Cluster, Diagram, Edge
from diagrams.aws.storage import S3
from diagrams.onprem.client import Client
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.network import Nginx
from diagrams.programming.language import Python

# Set the output path to docs/assets/
output_path = os.path.join(os.path.dirname(__file__), "assets", "architecture_diagram")

graph_attr = {"fontsize": "24", "bgcolor": "transparent", "pad": "0.5"}

with Diagram(
    "Antigravity Base Agentic Environment", show=False, filename=output_path, graph_attr=graph_attr, outformat="png"
):
    user = Client("Agentic Interface")

    with Cluster("Control Plane (.agents/)"):
        rules = Python("Governance Rules\n(12-Factor, Idempotency)")
        workflows = Python("CI/CD Workflows\n(Publish, Sync)")
        skills = Python("Skills\n(DuckDB Optimizer)")

        control_group = [rules, workflows, skills]

    with Cluster("Application (src/)"):
        router = Nginx("FastAPI Gateway")
        compactor = Python("Context Compactor")
        judge = Python("LLM-as-a-Judge\n(Eval Suite)")

        app_group = [router, compactor, judge]

    with Cluster("Data Plane (.antigravity/ & data/)"):
        duckdb = PostgreSQL("DuckDB Telemetry\n(Idempotent INSERT)")
        dlq = S3("Parquet DLQ\n(Quarantine)")

        data_group = [duckdb, dlq]

    # Connections
    user >> Edge(label="Executes Workflow") >> workflows
    workflows >> Edge(label="Applies Rules") >> rules
    rules >> Edge(label="Governs Router") >> router

    user >> Edge(label="Sends Telemetry") >> router
    router >> Edge(label="Validates & Compacts") >> compactor
    compactor >> Edge(label="Evaluates Quality") >> judge

    judge >> Edge(label="Logs Metrics") >> duckdb
    router >> Edge(label="Routes Invalid") >> dlq
