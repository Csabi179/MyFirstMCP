import json
import sys
from pathlib import Path

import anyio
from dotenv import load_dotenv
from mcp import Client, StdioServerParameters

from providers.base import ChatMessage, ToolSpec
from providers.factory import create_provider


load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parent
MAX_TOOL_ITERATIONS = 5


def mcp_result_to_text(result) -> str:
    """Convert an MCP result to provider-independent text."""

    if result.structured_content is not None:
        payload = {
            "is_error": result.is_error,
            "result": result.structured_content,
        }
    else:
        payload = {
            "is_error": result.is_error,
            "content": [
                item.text
                for item in result.content
                if hasattr(item, "text")
            ],
        }

    return json.dumps(
        payload,
        ensure_ascii=False,
    )


async def run_agent(user_prompt: str) -> str:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["server.py"],
        cwd=PROJECT_DIR,
    )

    provider = create_provider()

    print(
        f"LLM provider: {provider.provider_name}"
    )
    print(
        f"Model: {provider.model_name}"
    )

    async with Client(server_params) as mcp_client:
        tools_response = await mcp_client.list_tools()

        tools = [
            ToolSpec(
                name=tool.name,
                description=tool.description or "",
                input_schema=tool.input_schema,
            )
            for tool in tools_response.tools
        ]

        available_tool_names = {
            tool.name
            for tool in tools_response.tools
        }

        print("\nMCP tools available to the model:")

        for tool in tools:
            print(
                f"- {tool.name}: "
                f"{tool.description}"
            )

        messages = [
            ChatMessage(
                role="system",
                content=(
                    "You are a helpful assistant. "
                    "When the user's request matches "
                    "an available tool, use that tool "
                    "instead of performing the operation "
                    "yourself."
                ),
            ),
            ChatMessage(
                role="user",
                content=user_prompt,
            ),
        ]

        for _ in range(MAX_TOOL_ITERATIONS):
            response = await provider.complete(
                messages=messages,
                tools=tools,
            )

            if not response.tool_calls:
                return response.text or ""

            messages.append(
                ChatMessage(
                    role="assistant",
                    content=response.text,
                    tool_calls=response.tool_calls,
                )
            )

            for tool_call in response.tool_calls:
                if tool_call.name not in available_tool_names:
                    raise ValueError(
                        "Model requested unknown tool: "
                        f"{tool_call.name}"
                    )

                print(
                    f"\nModel selected tool: "
                    f"{tool_call.name}"
                    f"({tool_call.arguments})"
                )

                tool_result = await mcp_client.call_tool(
                    tool_call.name,
                    tool_call.arguments,
                )

                tool_result_text = mcp_result_to_text(
                    tool_result
                )

                print(
                    f"MCP tool result: "
                    f"{tool_result_text}"
                )

                messages.append(
                    ChatMessage(
                        role="tool",
                        content=tool_result_text,
                        tool_call_id=tool_call.id,
                        name=tool_call.name,
                    )
                )

        return (
            "The agent reached the maximum number "
            "of tool iterations."
        )


async def main() -> None:
    user_prompt = input("You: ").strip()

    if not user_prompt:
        print("Please enter a question.")
        return

    answer = await run_agent(
        user_prompt
    )

    print(f"\nAssistant: {answer}")


if __name__ == "__main__":
    anyio.run(main)