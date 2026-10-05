# MyFirstMCP

A small learning project that demonstrates how to build a local Model Context Protocol (MCP) server in Python and connect it to multiple online LLM providers.

The main goal of the project is to keep the MCP server independent from the selected LLM provider.

## Architecture

```text
                         agent.py
                            |
                       LLMProvider
                  +---------+---------+
                  |                   |
                  v                   v
             GroqProvider        GeminiProvider
                  |                   |
             GPT-OSS 120B       Gemini Flash
                  |                   |
                  +---------+---------+
                            |
                       MCP Client
                            |
                       MCP / stdio
                            |
                            v
                       server.py
                  +---------+---------+
                  |                   |
                  v                   v
                 add             count_words
```

The MCP server does not know which LLM or provider is being used.

## Features

- Python MCP server
- stdio MCP transport
- dynamic MCP tool discovery
- automatic LLM tool selection
- Groq provider support
- Google Gemini provider support
- provider-independent agent layer
- environment-based provider and model selection
- separate learning examples

## Project Structure

```text
MyFirstMCP/
|
|-- agent.py
|-- server.py
|-- requirements.txt
|-- .env.example
|-- .gitignore
|-- README.md
|
|-- providers/
|   |-- __init__.py
|   |-- base.py
|   |-- factory.py
|   |-- groq_provider.py
|   `-- gemini_provider.py
|
`-- examples/
    |-- client.py
    |-- client_stdio.py
    |-- llm_test.py
    `-- gemini_test.py
```

## Core Files

### `server.py`

The MCP server.

It exposes the MCP tools:

- `add`
- `count_words`

The server contains no Groq- or Gemini-specific code.

### `agent.py`

The main command-line application.

It:

1. starts the MCP server over stdio
2. discovers available MCP tools
3. loads the configured LLM provider
4. sends the available tools to the model
5. executes requested MCP tools
6. sends tool results back to the model
7. prints the final answer

### `providers/base.py`

Defines the provider-independent data structures and interface:

- `ToolSpec`
- `ToolCall`
- `ChatMessage`
- `ModelResponse`
- `LLMProvider`

### `providers/factory.py`

Selects the active provider from environment variables.

### `providers/groq_provider.py`

Adapter between the provider-independent agent format and the Groq API.

### `providers/gemini_provider.py`

Adapter between the provider-independent agent format and the Google Gemini API.

## MCP Tools

### `add`

Adds two integer numbers.

Example:

```text
User: What is 321 + 654?
Tool: add({"a": 321, "b": 654})
Result: 975
```

### `count_words`

Counts the words in a text.

Example:

```text
User: How many words are in: Apple pear peach plum
Tool: count_words({"text": "Apple pear peach plum"})
Result: 4
```

## Requirements

- Python 3.10 or newer
- Git
- Internet connection for online LLM providers
- a Groq API key and/or a Google Gemini API key

This project was developed with Python 3.12.

## Installation

Clone the repository:

```powershell
git clone https://github.com/Csabi179/MyFirstMCP.git
cd MyFirstMCP
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Configuration

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Add your API key or keys to `.env`.

### Groq

```text
GROQ_API_KEY=your_real_groq_api_key

LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-120b
```

### Google Gemini

```text
GEMINI_API_KEY=your_real_gemini_api_key

LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.5-flash-lite
```

The `.env` file is ignored by Git and must never be committed.

## Run the Agent

```powershell
python agent.py
```

Example:

```text
You: Mennyi 321 és 654 összege?

LLM provider: gemini
Model: gemini-3.5-flash-lite

MCP tools available to the model:
- add: Add two integer numbers.
- count_words: Count the number of words in a text.

Model selected tool: add({'a': 321, 'b': 654})
MCP tool result: {"is_error": false, "result": {"result": 975}}

Assistant: 321 és 654 összege 975.
```

## Switching Providers

No Python code needs to be changed.

To use Groq:

```text
LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-120b
```

To use Gemini:

```text
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.5-flash-lite
```

The same `agent.py`, MCP client, MCP server, and MCP tools are used with both providers.

## Learning Examples

The `examples/` directory contains the smaller programs used while building the project.

### `examples/client.py`

Tests the MCP server in-process.

### `examples/client_stdio.py`

Starts `server.py` as a separate subprocess and communicates with it over MCP stdio.

### `examples/llm_test.py`

Minimal Groq API connection test.

### `examples/gemini_test.py`

Minimal Gemini API connection test.

These files are useful for learning and diagnostics, but they are not required by the main application.

## Security

Never commit:

- `.env`
- API keys
- access tokens
- passwords

Only `.env.example` belongs in the repository.

## Dependencies

Main dependencies:

- MCP Python SDK
- Groq Python SDK
- Google GenAI Python SDK
- python-dotenv

Exact versions are stored in `requirements.txt`.

## What This Project Demonstrates

The project separates three responsibilities:

```text
MCP server
    |
    | exposes tools
    v
MCP client / agent
    |
    | orchestrates tool calls
    v
LLM provider adapter
```

Because of this separation:

- the MCP server is not tied to Groq
- the MCP server is not tied to Gemini
- the agent does not contain provider-specific API logic
- models can be changed through configuration
- new providers can be added by implementing another provider adapter

## Status

Working proof of concept with:

- MCP stdio server
- two MCP tools
- Groq / GPT-OSS support
- Google Gemini support
- automatic tool selection
- provider-independent agent architecture
