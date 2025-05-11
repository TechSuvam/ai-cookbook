import asyncio
import json
import os
from contextlib import AsyncExitStack
from typing import Any, Dict, List

import nest_asyncio
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import google.generativeai as genai

# Apply nest_asyncio to allow nested event loops (needed for Jupyter/IPython)
nest_asyncio.apply()

# Load environment variables
load_dotenv("../.env")

# Configure Gemini API
genai.configure(api_key="")
model = "gemini-2.5-pro-exp-03-25"

# Global variables to store session state
session = None
exit_stack = AsyncExitStack()
stdio = None
write = None


async def connect_to_server(server_script_path: str = "server.py"):
    """Connect to an MCP server."""
    global session, stdio, write, exit_stack

    server_params = StdioServerParameters(
        command="python",
        args=[server_script_path],
    )

    stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
    stdio, write = stdio_transport
    session = await exit_stack.enter_async_context(ClientSession(stdio, write))

    await session.initialize()

    tools_result = await session.list_tools()
    print("\nConnected to server with tools:")
    for tool in tools_result.tools:
        print(f"  - {tool.name}: {tool.description}")


async def get_mcp_tools() -> List[Dict[str, Any]]:
    """Get available tools from the MCP server."""
    global session
    tools_result = await session.list_tools()
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema,
        }
        for tool in tools_result.tools
    ]


async def process_query(query: str) -> str:
    """Process a query using Gemini and available MCP tools."""
    global session

    tools = await get_mcp_tools()
    tool_names = [tool["name"] for tool in tools]

    # Compose a system prompt to instruct Gemini to call tools by name if needed
    system_prompt = (
        "You are an assistant with access to the following tools:\n"
        + "\n".join([f"- {tool['name']}: {tool['description']}" for tool in tools])
        + "\nIf you need to use a tool, respond with:\n"
        + '{"tool_call": {"name": "<tool_name>", "arguments": {...}}}\n'
        + "Otherwise, answer directly."
    )

    # Send the user query to Gemini
    gemini_model = genai.GenerativeModel(model)
    response = await gemini_model.generate_content_async(
        [
            {"role": "user", "parts": [system_prompt + "\n\n" + query]},
        ]
    )

    # Try to parse a tool call from Gemini's response
    content = response.text.strip()
    try:
        # Look for a tool call in JSON format
        tool_call = json.loads(content).get("tool_call")
        if tool_call and tool_call["name"] in tool_names:
            # Call the tool on the MCP server
            result = await session.call_tool(
                tool_call["name"],
                arguments=tool_call.get("arguments", {}),
            )
            tool_response = result.content[0].text

            # Send the tool result back to Gemini for a final answer
            followup = (
                f"The tool '{tool_call['name']}' returned: {tool_response}\n"
                "Please answer the user's question using this information."
            )
            final_response = await gemini_model.generate_content_async(
                [
                    {"role": "user", "parts": [
                        system_prompt + "\n\n"
                        + query + "\n\n"
                        + f"Tool response: {tool_response}\n\n"
                        + followup
                    ]},
                ]
            )
            return final_response.text.strip()
    except Exception:
        pass  # Not a tool call, or parsing failed

    # If not a tool call, return Gemini's direct answer
    return content


async def cleanup():
    """Clean up resources."""
    global exit_stack
    await exit_stack.aclose()


async def main():
    """Main entry point for the client."""
    await connect_to_server("server.py")

    query = "What is our company's vacation policy?"
    print(f"\nQuery: {query}")

    response = await process_query(query)
    print(f"\nResponse: {response}")

    await cleanup()

if __name__ == "__main__":
    asyncio.run(main())
