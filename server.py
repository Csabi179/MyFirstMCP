from mcp.server import MCPServer


mcp = MCPServer("MyFirstMCP")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integer numbers."""
    return a + b


@mcp.tool()
def count_words(text: str) -> int:
    """Count the number of words in a text."""
    return len(text.split())


if __name__ == "__main__":
    mcp.run()