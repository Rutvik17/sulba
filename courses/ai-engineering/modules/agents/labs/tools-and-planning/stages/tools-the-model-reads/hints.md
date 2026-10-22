`self.search.find(query, service)` gives the passages as `search_help` lists them, each with its id under `passage`, its page's title under `page` and its text.

---

`json.loads` raises `json.JSONDecodeError` for text that isn't JSON, and gives a list, a number or a string for JSON that isn't an object: both get the same error.

---

Check the arguments in the order the errors are listed: the required ones first, from the spec's `required`, then each argument given, against the spec's `properties`. A property's `enum`, when it has one, lists the values it allows; `json.dumps(value)` shows a value as the model wrote it.
