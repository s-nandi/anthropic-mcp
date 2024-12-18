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
    --tool "npx -y @modelcontextprotocol/server-brave-search"
```