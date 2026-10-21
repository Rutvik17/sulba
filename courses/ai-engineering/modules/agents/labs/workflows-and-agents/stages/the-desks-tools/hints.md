`TOOLS[name]["parameters"]` has the arguments a tool takes, under `properties`, and those it must have, under `required`.

---

`json.loads` raises `json.JSONDecodeError` for text that isn't JSON, and gives a list or a number for JSON that isn't an object. An empty string is no arguments at all.

---

Once the arguments are checked, `getattr(self, name)(**given)` runs the tool by its name.
