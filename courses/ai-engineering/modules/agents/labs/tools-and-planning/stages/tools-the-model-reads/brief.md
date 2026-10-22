The model reads every tool result and every error as text, and its next step comes from what it reads. This lab writes the help desk's tools for that reader. `desk.py` has Retrieval's fused search, in `Search`, the caller's tickets, booked callbacks and the advisers' free times, in `Desk`, and the desk's own writes, `open_ticket`, `book_callback` and `cancel_callback`, which the model never calls. `TOOLS` describes the two tools the model can call, and `EXAMPLES` gives a call of each that fits.

In `Desk`, write the two tools, each of which gives text:

- `search_help(query, service=None)` gives a line, `f"{n} passages from {where}, best first. Cite each one you use by its id in square brackets, like [{first}]."`, where `where` is `the Social Security pages`, for one service, or `every service's pages`, and `first` is the first passage's id. Then, after a blank line, each passage the search finds, as its id in square brackets, a space and its page's title, a newline and its text, with a blank line between passages.
- `list_tickets(status="open")` gives `The caller's open tickets:` and a line for each, such as `T-2101: Social Security, Replacement card`, or `The caller has no open tickets.` When the caller has tickets with the other status, a last line says so: `They have 1 closed ticket: list_tickets with status "closed" lists them.`

Then `run(handlers, specs, examples, name, arguments)`, which runs a tool a model called, given each tool's function by its name, the tools' specs, an example call of each, the tool's name and the arguments the model wrote as JSON text. It runs the call once it fits the spec and gives the result. It never raises: a call that doesn't fit gives an error that says how to call again, in the first of these that applies:

- a name with no spec: `Error: there is no tool named 'open_ticket'. The tools are search_help, list_tickets.`
- arguments that aren't one JSON object: `Error: search_help's arguments are one JSON object, like {"query": "replace a lost card", "service": "ssa"}, and these aren't.`
- a required argument missing: `Error: search_help needs query, what to search for, in the caller's words. For example: {...}`, with the argument's description and the example;
- an argument the tool doesn't take: `Error: search_help takes no page. It takes query, service, like {...}`
- a value that isn't a string, or isn't one of the values its spec allows: `Error: service is ssa, va, studentaid, dmv, not "SSA".`, or `Error: query is a string, not 5.`
- a `ToolError` the tool raises: `Error: ` and its message.

`Desk.call(name, arguments)` runs the model's call with `run` and the desk's tools.

```
search_help(query, service=None) -> str
list_tickets(status="open") -> str
run(handlers, specs, examples, name, arguments) -> str
```

`uv run sulba.py model` serves the lab's two models on your machine, Qwen3.5-4B and nomic-embed-text-v1.5, at `http://127.0.0.1:9931/v1`, each by its name. The tests call a scripted model instead.
