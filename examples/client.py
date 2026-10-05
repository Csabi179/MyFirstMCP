import sys
from pathlib import Path

import anyio
from mcp import Client


PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from server import mcp


async def main() -> None:
    async with Client(mcp) as client:
        tools = await client.list_tools()

        print("Available tools:")

        for tool in tools.tools:
            print(f"- Name: {tool.name}")
            print(f"  Description: {tool.description}")
            print(f"  Input schema: {tool.input_schema}")
            print(f"  Output schema: {tool.output_schema}")

        print()

        result = await client.call_tool(
            "add",
            {
                "a": 5,
                "b": 7,
            },
        )

        print("Tool result:")
        print(f"  Error: {result.is_error}")
        print(f"  Content: {result.content}")
        print(
            f"  Structured content: "
            f"{result.structured_content}"
        )


if __name__ == "__main__":
    anyio.run(main)