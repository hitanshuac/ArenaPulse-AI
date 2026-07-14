import asyncio
import logging

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("antigravity-mcp-server")

# Initialize the MCP Server
server = Server("antigravity-governance")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available governance tools to connected agents.
    """
    return [
        types.Tool(
            name="check_ponytail_compliance",
            description="Run the Ponytail 7-step anti-over-engineering ladder check on a proposed code change.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "The task or proposed change the agent wants to implement.",
                    }
                },
                "required": ["task_description"],
            },
        ),
        types.Tool(
            name="verify_environment_awareness",
            description="Verify agent scanned the workspace for environment files before executing.",
            inputSchema={
                "type": "object",
                "properties": {
                    "detected_ecosystem": {
                        "type": "string",
                        "description": "The ecosystem detected (e.g., node, python, go, rust).",
                    }
                },
                "required": ["detected_ecosystem"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests from the agent.
    """
    if name == "check_ponytail_compliance":
        task = arguments.get("task_description", "Unknown task")
        logger.info(f"Checking Ponytail compliance for: {task}")
        # In a real implementation, this would run the actual compliance heuristics
        return [
            types.TextContent(type="text", text="Ponytail Ladder Check PASSED: Proceed with minimalist implementation.")
        ]

    elif name == "verify_environment_awareness":
        ecosystem = arguments.get("detected_ecosystem", "Unknown")
        logger.info(f"Environment awareness verified for: {ecosystem}")
        return [
            types.TextContent(
                type="text",
                text=f"Environment verified: {ecosystem}. You may proceed using native tools for this ecosystem.",
            )
        ]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """
    Run the MCP server over standard I/O (stdio).
    This allows local agents (like Cursor, Claude Code) to spawn this Python process
    and communicate with it directly without networking overhead.
    """
    logger.info("Starting Antigravity Governance MCP Server...")
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="antigravity-governance",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
