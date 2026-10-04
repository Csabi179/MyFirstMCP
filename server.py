from mcp.server import MCPServer


mcp = MCPServer("MyFirstMCP")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integer numbers."""
    return a + b


if __name__ == "__main__":
    mcp.run()