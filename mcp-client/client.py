import asyncio
import argparse
import os
import copy
from dataclasses import dataclass
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

MAX_INPUT_TOKENS = 1000
MAX_OUTPUT_TOKENS = 1000

@dataclass
class ToolCommand:
    command: str
    args: list[str]

def parse_tool_command(flag: str) -> ToolCommand:
    parts = flag.split(" ")
    return ToolCommand(parts[0], parts[1:])

@dataclass
class QueryResponse:
    text: str
    messages: list[str]

def truncated_to(messages: list[dict], max_tokens: int) -> list[dict]:
    truncated_messages = []
    total_length = 0
    for msg in reversed(messages):
        new_length = total_length + len(msg["content"])
        if new_length > max_tokens:
            break
        total_length = new_length
        truncated_messages.append(msg)
    return list(reversed(truncated_messages))

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.sessions = {}  # Map of command -> ClientSession
        self.tool_to_server = {}  # Map of tool name to server command
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()

    async def connect_to_servers(self, toolCommands: list[ToolCommand]):
        """Connect to multiple MCP servers
        
        Args:
            toolCommands: List of ToolCommand objects
        """
        print(toolCommands)
        # Process commands in order but store them in reverse
        # This ensures the first server stays active
        for toolCommand in toolCommands:
            server_params = StdioServerParameters(
                command=toolCommand.command,
                args=toolCommand.args,
                env=dict(os.environ),
            )
            
            # Create a new exit stack for each server
            stack = await self.exit_stack.enter_async_context(AsyncExitStack())
            stdio_transport = await stack.enter_async_context(stdio_client(server_params))
            stdio, write = stdio_transport
            session = await stack.enter_async_context(ClientSession(stdio, write))
            
            await session.initialize()
            
            # Store session with its command as key
            cmd_key = f"{toolCommand.command} {' '.join(toolCommand.args)}"
            
            # Store the new session first
            new_sessions = {cmd_key: session}
            new_sessions.update(self.sessions)
            self.sessions = new_sessions
            
            # List available tools for this server
            response = await session.list_tools()
            tools = response.tools
            
            # Map tool names to server command
            for tool in tools:
                if tool.name in self.tool_to_server:
                    raise ValueError(f"Duplicate tool name: {tool.name}")
                self.tool_to_server[tool.name] = cmd_key
            
            print(f"\nConnected to server '{cmd_key}' with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str, previous_messages = None) -> QueryResponse:
        """Process a query using Claude and available tools from all connected servers"""
        if previous_messages is None:
            previous_messages = []
        previous_messages = truncated_to(previous_messages, MAX_INPUT_TOKENS)

        messages = [
            {
                "role": "user",
                "content": query
            }
        ]
        # Collect tools from all connected servers
        available_tools = []
        for cmd, session in self.sessions.items():
            response = await session.list_tools()
            server_tools = [{ 
                "name": tool.name,
                "description": f"[Server: {cmd}] {tool.description}",
                "input_schema": tool.inputSchema
            } for tool in response.tools]
            available_tools.extend(server_tools)

        # Initial Claude API call
        response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=MAX_OUTPUT_TOKENS,
            messages=previous_messages+messages,
            tools=available_tools
        )

        # Process response and handle tool calls
        tool_results = []
        final_text = []

        for content in response.content:
            if content.type == 'text':
                final_text.append(content.text)
            elif content.type == 'tool_use':
                tool_name = content.name
                tool_args = content.input
                
                # Get server command for this tool
                server_cmd = self.tool_to_server.get(tool_name)
                if server_cmd:
                    session = self.sessions[server_cmd]
                    
                    # Execute tool call on the appropriate server
                    result = await session.call_tool(tool_name, tool_args)
                    tool_results.append({"call": tool_name, "result": result})
                    final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                    # Continue conversation with tool results
                    if hasattr(content, 'text') and content.text:
                        messages.append({
                          "role": "assistant",
                          "content": content.text
                        })

                    messages.append({
                        "role": "user", 
                        "content": result.content
                    })

                    # Get next response from Claude
                    response = self.anthropic.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=MAX_OUTPUT_TOKENS,
                        messages=previous_messages+messages,
                    )

                    final_text.append(response.content[0].text)

        final_content = "\n".join(final_text)
        messages.append({
            "role": "assistant",
            "content": final_content,
        })
        return QueryResponse(
            text=final_content,
            messages=messages,
        )

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        conversation = []
        while True:
            try:
                query = input("> ").strip()
                
                # Echo the input if it's coming from a pipe/file rather than terminal
                if not sys.stdin.isatty():
                    print(f"{query}")

                if query.lower() == 'quit':
                    break
                    
                response = await self.process_query(query, previous_messages=conversation)
                print("\n< " + response.text)
                conversation += response.messages
            except EOFError:
                print("\nReceived EOF, exiting gracefully...")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tool",
        help="MCP tool description, ex. \"uvx mcp-server-time --local-timezone America/Los_Angeles\"",
        type=str,
        action="append",
    )
    args = parser.parse_args()

    tools = args.tool
    if tools is None:
        tools = []
    tool_commands = [parse_tool_command(tool) for tool in tools]
        
    client = MCPClient()
    try:
        await client.connect_to_servers(tool_commands)
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
