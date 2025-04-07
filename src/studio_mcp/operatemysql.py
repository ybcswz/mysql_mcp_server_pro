import asyncio
import os
from mysql.connector import connect, Error
from mcp.server import Server
from mcp.types import  Tool, TextContent
from pypinyin import pinyin, Style


def get_db_config():
    """从环境变量获取数据库配置信息

    返回:
        dict: 包含数据库连接所需的配置信息
        - host: 数据库主机地址
        - port: 数据库端口
        - user: 数据库用户名
        - password: 数据库密码
        - database: 数据库名称

    异常:
        ValueError: 当必需的配置信息缺失时抛出
    """
    config = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE")
    }

    if not all([config["user"], config["password"], config["database"]]):
        raise ValueError("缺少必需的数据库配置")

    return config


def get_chinese_initials(text) -> list[TextContent]:
    """将中文文本转换为拼音首字母

    参数:
        text (str): 要转换的中文文本，以中文逗号分隔

    返回:
        list[TextContent]: 包含转换结果的TextContent列表
        - 每个词的首字母会被转换为大写
        - 多个词的结果以英文逗号连接

    示例:
        >>> get_chinese_initials("用户名，密码")
        [TextContent(type="text", text="YHM,MM")]
    """
    # 将文本按逗号分割
    words = text.split('，')

    # 存储每个词的首字母
    initials = []

    for word in words:
        # 获取每个字的拼音首字母
        word_pinyin = pinyin(word, style=Style.FIRST_LETTER)
        # 将每个字的首字母连接起来
        word_initials = ''.join([p[0].upper() for p in word_pinyin])
        initials.append(word_initials)

    # 用逗号连接所有结果
    return [TextContent(type="text", text=','.join(initials))]

def execute_sql(query : str) -> list[TextContent]:
    """执行SQL查询语句

    参数:
        query (str): 要执行的SQL语句，支持多条语句以分号分隔

    返回:
        list[TextContent]: 包含查询结果的TextContent列表
        - 对于SELECT查询：返回CSV格式的结果，包含列名和数据
        - 对于SHOW TABLES：返回数据库中的所有表名
        - 对于其他查询：返回执行状态和影响行数
        - 多条语句的结果以"---"分隔

    异常:
        Error: 当数据库连接或查询执行失败时抛出
    """
    config = get_db_config()
    try:
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                # 处理多条SQL语句
                statements = [stmt.strip() for stmt in query.split(';') if stmt.strip()]
                results = []

                for statement in statements:
                    try:
                        cursor.execute(statement)

                        # 特殊处理SHOW TABLES命令
                        if statement.strip().upper().startswith("SHOW TABLES"):
                            # 获取所有表名
                            tables = cursor.fetchall()
                            # 创建表头，格式为 "Tables_in_数据库名"
                            result = ["Tables_in_" + config["database"]]  # 表头
                            # 将表名添加到结果列表中
                            result.extend([table[0] for table in tables])
                            # 将结果转换为字符串并添加到最终结果列表中
                            results.append("\n".join(result))

                        # 处理SELECT查询
                        elif statement.strip().upper().startswith("SELECT"):
                            # 获取列名
                            columns = [desc[0] for desc in cursor.description]
                            # 获取所有行数据
                            rows = cursor.fetchall()
                            # 将每行数据转换为逗号分隔的字符串
                            result = [",".join(map(str, row)) for row in rows]
                            # 将列名和数据合并为CSV格式
                            results.append("\n".join([",".join(columns)] + result))

                        # 处理非SELECT查询
                        else:
                            conn.commit()
                            results.append(f"查询执行成功。影响行数: {cursor.rowcount}")

                    except Error as stmt_error:
                        # 单条语句执行出错时，记录错误并继续执行
                        results.append(f"执行语句出错: {str(stmt_error)}")

                return [TextContent(type="text", text="\n---\n".join(results))]

    except Error as e:
        print(f"执行SQL '{query}' 时出错: {e}")
        return [TextContent(type="text", text=f"执行查询时出错: {str(e)}")]

def get_table_name(text : str) -> list[TextContent]:
    """根据表的中文注释搜索数据库中的表名

    参数:
        text (str): 要搜索的表中文注释关键词

    返回:
        list[TextContent]: 包含查询结果的TextContent列表
        - 返回匹配的表名、数据库名和表注释信息
        - 结果以CSV格式返回，包含列名和数据

    示例:
        >>> get_table_name("用户")
        [TextContent(type="text", text="TABLE_SCHEMA,TABLE_NAME,TABLE_COMMENT\ndb_name,user_table,用户信息表")]
    """
    config = get_db_config()
    sql = "SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_COMMENT "
    sql += f"FROM information_schema.TABLES WHERE TABLE_SCHEMA = '{config["database"]}' AND TABLE_COMMENT LIKE '%{text}%';"
    return execute_sql(sql)

def get_table_desc(text : str) -> list[TextContent]:
    """获取指定表的所有字段信息

    参数:
        text (str): 要查询的表名

    返回:
        list[TextContent]: 包含查询结果的TextContent列表
        - 返回表的字段名和字段注释信息
        - 结果以CSV格式返回，包含列名和数据

    示例:
        >>> get_table_desc("user_table")
        [TextContent(type="text", text="COLUMN_NAME,COLUMN_COMMENT\nid,主键\nusername,用户名")]
    """
    config = get_db_config()
    sql = "SELECT COLUMN_NAME,COLUMN_COMMENT "
    sql += f"FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '{config["database"]}' "
    sql += f"AND TABLE_NAME = '{text}';"
    return execute_sql(sql)

# 初始化服务器
app = Server("operateMysql")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用的MySQL工具

    返回:
        list[Tool]: 工具列表，当前仅包含execute_sql工具
    """
    return [
        Tool(
            name="execute_sql",
            description="在MySQL5.6s数据库上执行SQL",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "要执行的SQL语句"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_chinese_initials",
            description="创建表结构时，将中文字段名转换为拼音首字母字段",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "要获取拼音首字母的汉字文本，以“,”分隔"
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="get_table_name",
            description="根据表中文名搜索数据库中对应的表名",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "要搜索的表中文名"
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="get_table_desc",
            description="根据表名搜索数据库中对应的表结构",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "要搜索的表名"
                    }
                },
                "required": ["text"]
            }
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:

    if name == "execute_sql":
        query = arguments.get("query")
        if not query:
            raise ValueError("缺少查询语句")
        return execute_sql(query)
    elif name == "get_chinese_initials":
        text = arguments.get("text")
        if not text:
            raise ValueError("缺少文本")
        return get_chinese_initials(text)
    elif name == "get_table_name":
        text = arguments.get("text")
        if not text:
            raise ValueError("缺少文本")
        return get_table_name(text)
    elif name == "get_table_desc":
        text = arguments.get("text")
        if not text:
            raise ValueError("缺少文本")
        return get_table_desc(text)

    raise ValueError(f"未知的工具: {name}")


async def main():
    """主入口函数，运行MCP服务器

    - 初始化数据库连接
    - 启动标准输入输出服务器
    - 运行应用服务器
    """
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        try:
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
        except Exception as e:
            print(f"服务器错误: {str(e)}")
            raise

if __name__ == "__main__":
    asyncio.run(main())
