# quickstart-resources
A repository of servers and clients from the Model Context Protocol tutorials

Based on: https://github.com/modelcontextprotocol/quickstart-resources/tree/main

First export environment variables:
```
export $(cat .env | xargs)
```

Run:
```
python mcp-client/client.py \
    --tool "uvx mcp-server-time --local-timezone America/Los_Angeles"
```