# quickstart-resources
A repository of servers and clients from the Model Context Protocol tutorials

Based on: https://github.com/modelcontextprotocol/quickstart-resources/tree/main

First export environment variables:
```
export $(cat .env | xargs)
```

Run:
```
python mcp-client/client.py weather-server-python/src/weather/server.py
```