import json
from typing import Any

from groq import AsyncGroq

from providers.base import (
    ChatMessage,
    ModelResponse,
    ToolCall,
    ToolSpec,
)


class GroqProvider:
    """Groq implementation of the provider-independent LLM interface."""

    provider_name = "groq"

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    @staticmethod
    def _tool_to_groq(tool: ToolSpec) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema,
            },
        }

    @staticmethod
    def _message_to_groq(message: ChatMessage) -> dict[str, Any]:
        if message.role in {"system", "user"}:
            return {
                "role": message.role,
                "content": message.content or "",
            }

        if message.role == "assistant":
            result: dict[str, Any] = {
                "role": "assistant",
            }

            if message.content is not None:
                result["content"] = message.content

            if message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.name,
                            "arguments": json.dumps(
                                tool_call.arguments,
                                ensure_ascii=False,
                            ),
                        },
                    }
                    for tool_call in message.tool_calls
                ]

            return result

        if message.role == "tool":
            return {
                "role": "tool",
                "tool_call_id": message.tool_call_id,
                "name": message.name,
                "content": message.content or "",
            }

        raise ValueError(
            f"Unsupported message role: {message.role}"
        )

    async def complete(
        self,
        messages: list[ChatMessage],
        tools: list[ToolSpec],
    ) -> ModelResponse:
        groq_messages = [
            self._message_to_groq(message)
            for message in messages
        ]

        groq_tools = [
            self._tool_to_groq(tool)
            for tool in tools
        ]

        async with AsyncGroq() as client:
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=groq_messages,
                tools=groq_tools,
                tool_choice="auto",
                temperature=0,
            )

        response_message = response.choices[0].message

        tool_calls = []

        for tool_call in response_message.tool_calls or []:
            tool_calls.append(
                ToolCall(
                    id=tool_call.id,
                    name=tool_call.function.name,
                    arguments=json.loads(
                        tool_call.function.arguments
                    ),
                )
            )

        return ModelResponse(
            text=response_message.content,
            tool_calls=tool_calls,
        )