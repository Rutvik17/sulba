The help desk of Retrieval and Evals answers people's questions about four US public services, Social Security, veterans' benefits, federal student aid and New York State's DMV, from their {% $fig.pages %} help pages. Now it does its own work too. A caller signs in, and has tickets, each about their own case with one service, which that service's advisers look into. The desk can open a ticket, and book an adviser to call the caller back about one of their open tickets, at a time that service's advisers are free: Monday 2 to Friday 6 November 2026, on the hour from 09:00 to 16:00.

This lab builds the desk two ways, as a workflow and as an agent, and both work through its tools. `desk.py` has Retrieval's fused search of the passages, in `Search`, and the tools' descriptions, in `TOOLS`. In `Desk`, write the tools, each of which gives a dictionary:

- `search_help(query, service=None)` gives `{"results": [...]}`, the passages `self.search.find` finds for the query, in the service's pages or in every page.
- `list_tickets()` gives `{"tickets": [...]}`, a copy of each of the caller's tickets.
- `open_ticket(service, summary)` opens a ticket for the service, with the summary, and gives its id, `{"ticket": "T-3001"}`: the first ticket the desk opens is T-3001, the next T-3002, and so on.
- `free_callbacks(service, day)` gives `{"day": day, "free": [...]}`, the times the service's advisers are free that day.
- `book_callback(ticket, day, time)` books an adviser of the ticket's service at that time, which is then no longer free, and gives `{"booked": {"ticket": ticket, "day": day, "time": time}}`.

A call that can't be done gives `{"error": "..."}`, a sentence that says why, and changes nothing: a service the desk doesn't have, a day it doesn't call back on, a summary of nothing but spaces, a ticket the caller doesn't have or that's closed, a time the advisers aren't free. Each ticket opened and each callback booked goes in `self.writes`, with the tool's name, the ticket, its service or its day and time, and `turn`, the caller's message the desk was answering, as the tests show.

Then `call(name, arguments)`, which runs a tool a model called, given its name and the arguments it wrote as JSON text, and gives the result as JSON text. It never raises. A name `TOOLS` doesn't have, arguments that aren't a JSON object, an argument missing or one the tool doesn't take, or one that isn't a string, gives the model an error to read instead.

```
search_help(query, service=None) -> dict
list_tickets() -> dict
open_ticket(service, summary) -> dict
free_callbacks(service, day) -> dict
book_callback(ticket, day, time) -> dict
call(name, arguments) -> str
```

`uv run sulba.py model` serves the lab's two models on your machine, Qwen3.5-4B and nomic-embed-text-v1.5, at `http://127.0.0.1:9931/v1`, each by its name. The tests call a scripted model instead.
