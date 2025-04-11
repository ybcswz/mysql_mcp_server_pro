from typing import Dict, Any, Sequence

from mcp.types import TextContent, Tool


class BaseHandler:

    name: str = ""
    description: str = ""

    def get_tool_description(self) -> Tool:
        raise NotImplementedError

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        raise NotImplementedError

