import json
from typing import Any

from google import genai
from google.genai import types

from providers.base import (
    ChatMessage,
    ModelResponse,
    ToolCall,
    ToolSpec,
)


class GeminiProvider:
    """Google Gemini implementation of the LLM provider interface."""

    provider_name = "gemini"

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

        self._client = genai.Client()
        self._chat = None
        self._processed_tool_messages = 0

    @staticmethod
    def _tool_to_gemini(
        tool: ToolSpec,
    ) -> types.FunctionDeclaration:
        return types.FunctionDeclaration(
            name=tool.name,
            description=tool.description,
            parameters_json_schema=tool.input_schema,
        )

    @staticmethod
    def _extract_text(response) -> str | None:
        if not response.candidates:
            return None

        content = response.candidates[0].content

        if content is None or not content.parts:
            return None

        texts = []

        for part in content.parts:
            if part.text and not part.thought:
                texts.append(part.text)

        if not texts:
            return None

        return "\n".join(texts)

    def _create_chat(
        self,
        messages: list[ChatMessage],
        tools: list[ToolSpec],
    ):
        system_instruction = ""

        for message in messages:
            if message.role == "system":
                system_instruction = message.content or ""
                break

        function_declarations = [
            self._tool_to_gemini(tool)
            for tool in tools
        ]

        gemini_tool = types.Tool(
            function_declarations=function_declarations
        )

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[gemini_tool],
            temperature=0,
            automatic_function_calling=(
                types.AutomaticFunctionCallingConfig(
                    disable=True
                )
            ),
        )

        return self._client.aio.chats.create(
            model=self.model_name,
            config=config,
        )

    @staticmethod
    def _tool_result_to_payload(
        message: ChatMessage,
    ) -> dict[str, Any]:
        content = message.content or "{}"

        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            return {
                "output": content,
            }

        if isinstance(payload, dict):
            return payload

        return {
            "output": payload,
        }

    async def complete(
        self,
        messages: list[ChatMessage],
        tools: list[ToolSpec],
    ) -> ModelResponse:
        if self._chat is None:
            self._chat = self._create_chat(
                messages=messages,
                tools=tools,
            )

            user_messages = [
                message
                for message in messages
                if message.role == "user"
            ]

            if not user_messages:
                raise ValueError(
                    "No user message was provided."
                )

            response = await self._chat.send_message(
                user_messages[-1].content or ""
            )

        else:
            tool_messages = [
                message
                for message in messages
                if message.role == "tool"
            ]

            new_tool_messages = tool_messages[
                self._processed_tool_messages:
            ]

            if not new_tool_messages:
                raise ValueError(
                    "Gemini expected a new tool result."
                )

            function_response_parts = []

            for message in new_tool_messages:
                function_response_parts.append(
                    types.Part.from_function_response(
                        name=message.name or "",
                        response=self._tool_result_to_payload(
                            message
                        ),
                    )
                )

            self._processed_tool_messages = len(
                tool_messages
            )

            response = await self._chat.send_message(
                function_response_parts
            )

        tool_calls = []

        for index, function_call in enumerate(
            response.function_calls or []
        ):
            tool_calls.append(
                ToolCall(
                    id=function_call.id or "",
                    name=function_call.name or "",
                    arguments=dict(
                        function_call.args or {}
                    ),
                )
            )

        return ModelResponse(
            text=self._extract_text(response),
            tool_calls=tool_calls,
        )