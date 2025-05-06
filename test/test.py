import asyncio
from mcp.client.sse import sse_client
from mcp import ClientSession


async def main():
    async with sse_client('http://localhost:9000/sse') as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()

            res = await session.call_tool(
                'execute_sql', {
   'query': 'select 1;',})
            print(res)


if __name__ == '__main__':
    asyncio.run(main())
