from typing import Dict, Any, Sequence

from mcp import Tool
from mcp.types import TextContent

from .base import BaseHandler
from config import get_db_config, get_schema
from handles import (
    ExecuteSQL
)


class GetSchema(BaseHandler):

    name = "get_schema"
    description = (
        "根据用户问题获取数据库schema"
    )

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "user_question": {
                        "type": "string",
                        "description": "用户问题"
                    }
                },
                "required": ["user_question"]
            }
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
            """根据用户问题获取数据库schema

            参数:
                user_question (str): 用户问题

            返回:
                list[TextContent]: 包含数据库schema的TextContent列表
                - 结果以字符串格式返回，包含表名、列名和表之间的外键关系
            """
            try:
                if "user_question" not in arguments:
                    raise ValueError("缺少用户问题")

                user_question = arguments["user_question"]

                return await get_schema(user_question)

            except Exception as e:
                return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]