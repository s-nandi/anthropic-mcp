# quickstart-resources
A repository of servers and clients from the Model Context Protocol tutorials

Based on: https://github.com/modelcontextprotocol/quickstart-resources/tree/main

First export environment variables:
```
export $(cat .env | xargs)
```
If you haven't set up `.env` yet, look at .env-example to see which API keys are required, and their corresponding environment variable names.

To run with a single tool, you can run:
```
python mcp-client/client.py \
    --tool "uvx mcp-server-time --local-timezone America/Los_Angeles"
```
This doesn't use the local server, and instead uses pip (or some other package manager).

Or
```
python mcp-client/client.py \
    --tool "uv run weather/src/weather/server.py"
```
This actually uses the local server implementation.

For a full client with every tool, run:
```
python mcp-client/client.py \
    --tool "uv run weather/src/weather/server.py" \
    --tool "uvx mcp-server-time --local-timezone America/Los_Angeles" \
    --tool "npx -y @modelcontextprotocol/server-brave-search" \
    --tool "npx -y @modelcontextprotocol/server-memory" \
    --tool "npx -y @modelcontextprotocol/server-filesystem $(realpath ./llm_scratch)"
```

To stdin from a separate terminal, you can first create a named pipe:
```
mkfifo mcp-pipe
```

Then run the following from one terminal:
```
cat mcp-pipe | python mcp-client/client.py \
    --tool "uv run weather/src/weather/server.py" \
    --tool "uvx mcp-server-time --local-timezone America/Los_Angeles" \
    --tool "npx -y @modelcontextprotocol/server-brave-search" \
    --tool "npx -y @modelcontextprotocol/server-memory" \
    --tool "npx -y @modelcontextprotocol/server-filesystem $(realpath ./llm_scratch)"
```

And send commands from another terminal:
```
cat > mcp-pipe
What tools do you have access to?
```
You can continue typing in this terminal, and the client will respond.
Closing this second terminal will automatically clean up both processes.

To clean up the pipe:
```
rm mcp-pipe
```