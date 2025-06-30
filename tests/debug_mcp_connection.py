#!/usr/bin/env python3
"""
Debug script to test MCP connection issues.
Compares working MCP call (via Cline) with our Python implementation.
"""

import asyncio
import sys
import traceback
from pathlib import Path
from typing import Optional, Any

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp import ClientSession
from mcp.client.sse import sse_client


async def test_direct_mcp_call() -> Optional[Any]:
    """Test the exact same MCP call that works via Cline."""

    url = "http://127.0.0.1:8052/sse"
    tool_name = "perform_rag_query"
    arguments = {
        "query": "Start-ADTMsiProcess Set-ADTRegistryKey Copy-ADTFile Write-ADTLogEntry",
        "source": "psappdeploytoolkit.com",
        "match_count": 5,
    }

    print(f"🔗 Connecting to MCP server at: {url}")
    print(f"🔧 Tool: {tool_name}")
    print(f"📋 Arguments: {arguments}")
    print("=" * 60)

    try:
        print("🌐 Opening SSE connection...")
        async with sse_client(url) as (read, write):
            print("✅ SSE connection established")

            print("🔐 Creating MCP session...")
            async with ClientSession(read, write) as session:
                print("✅ MCP session created")

                print("🚀 Initializing session...")
                await session.initialize()
                print("✅ Session initialized")

                print("📞 Calling tool...")
                result = await session.call_tool(tool_name, arguments)
                print("✅ Tool call completed")

                if result.isError:
                    print(f"❌ Tool call failed: {result.content}")
                    return None
                else:
                    print("🎉 Tool call successful!")
                    response = result.structuredContent or result.content
                    print(f"📄 Response type: {type(response)}")
                    print(f"📄 Response preview: {str(response)[:200]}...")
                    return response

    except Exception as e:
        print(f"💥 Error occurred: {type(e).__name__}: {str(e)}")
        print("🔍 Full traceback:")
        traceback.print_exc()
        return None


async def test_session_listing() -> Optional[Any]:
    """Test if we can list available tools."""

    url = "http://127.0.0.1:8052/sse"

    print("\n" + "=" * 60)
    print("🔍 Testing tool discovery...")

    try:
        async with sse_client(url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Try to list tools
                tools = await session.list_tools()
                print(f"📋 Available tools: {len(tools)}")
                for tool in tools:
                    print(f"  - {tool.name}: {tool.description}")

                return tools

    except Exception as e:
        print(f"💥 Tool listing failed: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("🧪 MCP Debug Test Script")
    print("Testing direct MCP connection to crawl4ai-rag server")

    # Test 1: Tool discovery
    print("\n📋 TEST 1: Tool Discovery")
    tools = asyncio.run(test_session_listing())

    # Test 2: Direct tool call
    print("\n📞 TEST 2: Direct Tool Call")
    response = asyncio.run(test_direct_mcp_call())

    if response:
        print("\n🎉 SUCCESS: MCP connection working!")
        print("The issue is likely in the integration with your application.")
    else:
        print("\n❌ FAILURE: MCP connection has issues.")
        print("Need to debug the connection protocol.")
