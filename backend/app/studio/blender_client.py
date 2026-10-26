"""The web worker is a real MCP stdio client for the bounded Blender server."""
import asyncio
import json
import os
import sys
from datetime import timedelta

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def server_parameters(root, executable):
    from backend.app.studio.service import REPO
    allowed = {'PATH', 'PATHEXT', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'USERPROFILE',
               'HOME', 'LOCALAPPDATA', 'APPDATA', 'PROGRAMFILES', 'OS', 'NUMBER_OF_PROCESSORS'}
    env = {k: v for k, v in os.environ.items() if k.upper() in allowed}
    env.update(BLENDER_ASSET_ROOT=str(root), BLENDER_EXECUTABLE=str(executable),
               PYTHONPATH=str(REPO), PYTHONIOENCODING='utf-8')
    return StdioServerParameters(command=sys.executable, args=['-m', 'backend.blender_mcp'], env=env, cwd=str(REPO))


async def call_tool(parameters, name, arguments):
    async with (stdio_client(parameters) as (reader, writer),
                ClientSession(reader, writer, read_timeout_seconds=timedelta(seconds=2900)) as client):
        await client.initialize()
        result = await client.call_tool(name, arguments=arguments)
        if result.isError:
            raise ValueError('Blender MCP preparation failed. Inspect the preserved local worker log.')
        if result.structuredContent:
            return result.structuredContent
        return json.loads(next(c.text for c in result.content if c.type == 'text'))


def prepare_via_mcp(root, executable, asset_id, revision, run_id):
    return asyncio.run(call_tool(server_parameters(root, executable), 'prepare_asset',
                                {'asset_id': asset_id, 'result_revision': revision, 'run_id': run_id}))
