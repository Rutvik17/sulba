The assistant's tests use values written in the tests themselves, and records they never look at again. Ask how the service will call each function: with values `json.loads` has just read, and records it still needs afterwards.

---

For each comparison, ask which Python operator it uses, `is`, `==` or `in`, and what that operator does with a number read from JSON, or with `True`.

---

For each test of a field, ask what it does with a field set to `0`, `""` or `False`.
