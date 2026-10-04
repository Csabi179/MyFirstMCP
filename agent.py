import json
import os
import sys
from pathlib import Path

import anyio
from dotenv import load_dotenv
from groq import AsyncGroq
from mcp import Client, StdioServerParameters


load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parent
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
MAX_TOOL_ITERATIONS = 5


def convert_mcp_tools_to_groq(mcp_tools):
    """Convert MCP tool definitions to Groq function-calling format."""

    groq_tools = []

    for tool in mcp_tools:
        groq_tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema,
                },
            }
        )

    return groq_tools


def mcp_result_to_text(result) -> str:
    """Convert an MCP tool result to text that can be sent to the LLM."""

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

    return json.dumps(payload, ensure_ascii=False)


async def run_agent(user_prompt: str) -> str:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["server.py"],
        cwd=PROJECT_DIR,
    )

    async with Client(server_params) as mcp_client:
        tools_response = await mcp_client.list_tools()

        groq_tools = convert_mcp_tools_to_groq(
            tools_response.tools
        )

        available_tool_names = {
            tool.name for tool in tools_response.tools
        }

        print("MCP tools available to the model:")

        for tool in tools_response.tools:
            print(f"- {tool.name}: {tool.description}")

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. "
                    "When the user's request matches an available tool, "
                    "use that tool instead of performing the operation "
                    "yourself."
                ),
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ]

        async with AsyncGroq() as groq_client:
            for iteration in range(MAX_TOOL_ITERATIONS):
                response = await groq_client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=groq_tools,
                    tool_choice="auto",
                    temperature=0,
                )

                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls or []

                if not tool_calls:
                    return response_message.content or ""

                messages.append(response_message)

                for tool_call in tool_calls:
                    tool_name = tool_call.function.name

                    if tool_name not in available_tool_names:
                        raise ValueError(
                            f"Model requested unknown tool: {tool_name}"
                        )

                    tool_arguments = json.loads(
                        tool_call.function.arguments
                    )

                    print(
                        f"\nModel selected tool: "
                        f"{tool_name}({tool_arguments})"
                    )

                    tool_result = await mcp_client.call_tool(
                        tool_name,
                        tool_arguments,
                    )

                    tool_result_text = mcp_result_to_text(
                        tool_result
                    )

                    print(
                        f"MCP tool result: {tool_result_text}"
                    )

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": tool_result_text,
                        }
                    )

            return (
                "The agent reached the maximum number "
                "of tool iterations."
            )


async def main() -> None:
    print(f"Model: {MODEL}")

    user_prompt = input("\nYou: ").strip()

    if not user_prompt:
        print("Please enter a question.")
        return

    answer = await run_agent(user_prompt)

    print(f"\nAssistant: {answer}")


if __name__ == "__main__":
    anyio.run(main)