An assistant that speaks the Model Context Protocol, MCP, can use the tools any MCP server offers: it asks the server for its tools, offers them to its model, and has the server run the calls the model makes. Over MCP's stdio transport, the assistant starts the server as a program of its own, writes it a JSON-RPC message on each line, and reads each reply from a line the server writes. Served that way, the shop's tools work with any assistant that speaks this version of MCP.

In `server.py`, write `Server(functions)`, whose `handle(line)` gives the reply to one line as a line of JSON, and `serve(server, lines, out)`, which writes each reply to `out` on a line of its own. The server speaks MCP's version `2026-07-28`, in which every request stands on its own:

```json
{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "opening_hours", "arguments": {"day": "Saturday"}, "_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {}}}}
{"jsonrpc": "2.0", "id": 1, "result": {"resultType": "complete", "content": [{"type": "text", "text": "\"9:00 to 13:00\""}], "isError": false, "_meta": {"io.modelcontextprotocol/serverInfo": {"name": "bike-shop", "version": "1.0.0"}}}}
```

- A request has `"jsonrpc": "2.0"`, an `id`, a string or an integer, a `method`, and, if it has any, `params`, an object. Its reply has `"jsonrpc": "2.0"`, the request's `id`, and a `result` or an `error`.
- A result has `"resultType": "complete"`, and `SERVER` as `io.modelcontextprotocol/serverInfo` in its `_meta`. An error has a `code` and a `message`.
- A message without an `id` is a notification, which gets no reply.
- Text that isn't JSON gets the error `-32700`, and a message that isn't a request `-32600`, with its `id` when it has one that's a string or an integer.
- A request's `_meta` carries its protocol version, `io.modelcontextprotocol/protocolVersion`, and the assistant's capabilities, `io.modelcontextprotocol/clientCapabilities`. A request without them gets `-32602`, and one for a version other than `VERSION` gets `-32022`, with `{"supported": [VERSION], "requested": ...}` as its `data`.
- `server/discover` gives `"supportedVersions": [VERSION]` and `"capabilities": {"tools": {}}`. `tools/list` gives `"tools"`: each tool's `name`, `description` and `inputSchema`, the schema of its parameters that your `describe` makes. Both give `"ttlMs": TTL`, how long the assistant may keep them, and `"cacheScope": "public"`, as they're the same for everyone.
- `tools/call` gives the tool's value as JSON text in its `content`, with `"isError": false`. When the `arguments` don't fit the tool's input schema, or the tool raises, the text says what went wrong, with `"isError": true`. An unknown tool, or a call without a `name` and an object of `arguments`, gets `-32602`.
- Any other method gets `-32601`.

```
Server(functions).handle(line) -> str | None
serve(server, lines, out)
```

Two tests run on every attempt. Then six checks run before the code ships.
