import sys
from pathlib import Path

import anyio
from mcp import Client, StdioServerParameters


PROJECT_DIR = Path(__file__).resolve().parent.parent


async def main() -> None:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["server.py"],
        cwd=PROJECT_DIR,
    )

    async with Client(server_params) as client:
        print(f"Protocol version: {client.protocol_version}")

        if client.server_info is not None:
            print(f"Server name: {client.server_info.name}")

        tools = await client.list_tools()

        print("\nAvailable tools:")

        for tool in tools.tools:
            print(f"- {tool.name}: {tool.description}")

        add_result = await client.call_tool(
            "add",
            {
                "a": 10,
                "b": 25,
            },
        )

        print("\nAdd tool result:")
        print(f"  Error: {add_result.is_error}")
        print(f"  Structured content: {add_result.structured_content}")

        word_count_result = await client.call_tool(
            "count_words",
            {
                "text": "Model Context Protocol is very interesting",
            },
        )

        print("\nCount words tool result:")
        print(f"  Error: {word_count_result.is_error}")
        print(
            f"  Structured content: "
            f"{word_count_result.structured_content}"
        )


if __name__ == "__main__":
    anyio.run(main)