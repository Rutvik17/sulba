A model reads the desk through tools: it names a tool, and writes its arguments as JSON text. In Python, the desk checked those arguments against each tool's JSON schema. In Java, each tool's arguments are a record, and the record's components say what the tool takes. In `Tools.java`, the starter gives you the types:

- `Action<A>`, an interface with one method, `run(A arguments)`, which gives the text the model reads, and may throw `Desk.Refused`.
- `Tool<A extends Record>(name, arguments, example, action)`, a tool: its name, the record class its arguments are read into, an example of its arguments as JSON, and its action.
- `ListTickets(status)` and `FreeTimes(service, day)`, the arguments of the desk's two tools.

Write `Tools`, made from a list of tools of any records, which refuses two with one name with an `IllegalArgumentException`: `Two tools are named repeat.` `names()` gives their names in order, and `forDesk(desk)` gives the desk's two tools:

- `list_tickets`, with the example `{"status": "open"}`, gives `desk.listTickets(status)`.
- `free_times`, with the example `{"service": "ssa", "day": "2026-11-03"}`, gives `The Social Security advisers are free on Monday 2026-11-02 at 09:00, 14:00.`, or `The veterans' benefits advisers aren't free on Monday 2026-11-02.`

`call(name, arguments)` runs the tool by that name with the arguments the model wrote, and gives its text. A call that can't run gives an error that tells the model how to call again, the first of these that fits, with the tool's example where it shows one:

| When | The text |
| --- | --- |
| No tool has the name | `Error: there is no tool named "book". The tools are list_tickets, free_times.` |
| The arguments aren't one JSON object | `Error: list_tickets's arguments are one JSON object, like {"status": "open"}, and these aren't.` |
| A key isn't one of the record's components | `Error: free_times takes no time. It takes service, day, like {"service": "ssa", "day": "2026-11-03"}.` |
| A component is missing, or `null` | `Error: free_times needs day. For example: {"service": "ssa", "day": "2026-11-03"}` |
| A value its component can't hold | `Error: day can't be "Monday". For example: {"service": "ssa", "day": "2026-11-03"}` |
| The record's constructor throws | `Error: ` and the exception's message |
| The action throws `Desk.Refused` | `Error: ` and the refusal's message |

Arguments that are blank count as `{}`. Any other exception from an action is a bug in the tool, so it isn't caught: it goes up to the caller.

```java
public Tools(List<Tool<?>> tools)
public static Tools forDesk(Desk desk)
public List<String> names()
public String call(String name, String arguments)
```

The tests make tools of their own records too, as `new Tools.Tool<>("repeat", Repeat.class, ..., arguments -> ...)`.
