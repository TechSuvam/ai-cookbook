# Gemini Integration with MCP

This section demonstrates how to integrate the Model Context Protocol (MCP) with Google's Gemini API to create a system where Gemini can access and use tools provided by your MCP server.

## Overview

This example shows how to:

1. Create an MCP server that exposes a knowledge base tool
2. Connect Gemini to this MCP server
3. Allow Gemini to dynamically use the tools when responding to user queries

## Connection Methods

This example uses the **stdio transport** for communication between the client and server, which means:

- The client and server run in the same process
- The client directly launches the server as a subprocess
- No separate server process is needed

If you want to split your client and server into separate applications (e.g., running the server on a different machine), you'll need to use the **SSE (Server-Sent Events) transport** instead. For details on setting up an SSE connection, see the [Simple Server Setup](../3-simple-server-setup) section.

### Data Flow Explanation

1. **User Query**: The user sends a query to the system (e.g., "What is our company's vacation policy?")
2. **Gemini API**: Gemini receives the query and available tools from the MCP server (via prompt engineering)
3. **Tool Suggestion**: Gemini may suggest using a tool based on the query
4. **MCP Client**: The client receives Gemini's tool call suggestion and forwards it to the MCP server
5. **MCP Server**: The server executes the requested tool (e.g., retrieving knowledge base data)
6. **Response Flow**: The tool result flows back through the MCP client to Gemini
7. **Final Response**: Gemini generates a final response incorporating the tool data

## How Gemini Executes Tools

Gemini does not natively support function calling like OpenAI. Instead, the client uses prompt engineering to instruct Gemini to suggest tool calls in a specific JSON format. The client then parses these suggestions, executes the tool via MCP, and provides the result back to Gemini for a final answer.

1. **Tool Registration**: The MCP client converts MCP tools to a format described in the prompt for Gemini
2. **Tool Suggestion**: Gemini suggests which tools to use based on the user query and prompt instructions
3. **Tool Execution**: The MCP client executes the selected tools and returns results
4. **Context Integration**: Gemini incorporates the tool results into its response

## The Role of MCP

MCP serves as a standardized bridge between AI models and your backend systems:

- **Standardization**: MCP provides a consistent interface for AI models to interact with tools
- **Abstraction**: MCP abstracts away the complexity of your backend systems
- **Security**: MCP allows you to control exactly what tools and data are exposed to AI models
- **Flexibility**: You can change your backend implementation without changing the AI integration

## Implementation Details

### Server (`server.py`)

The MCP server exposes a `get_knowledge_base` tool that retrieves Q&A pairs from a JSON file.

### Client (`client-simple.py`)

The client:

1. Connects to the MCP server
2. Describes MCP tools to Gemini via prompt engineering
3. Handles the communication between Gemini and the MCP server
4. Processes tool results and generates final responses

### Knowledge Base (`data/kb.json`)

Contains Q&A pairs about company policies that can be queried through the MCP server.

## Running the Example

1. Ensure you have the required dependencies installed
2. Set up your Gemini API key in the `.env` file as `GOOGLE_API_KEY`
3. Run the client: `python client-simple.py`

Note: With the stdio transport used in this example, you don't need to run the server separately as the client will automatically start it.
