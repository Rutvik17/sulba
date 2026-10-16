`check_code` awaits the lookup, `if await registry.lookup(code):`, and returns `None` or the message.

---

A comprehension in an `async def` function can await: `[await check_code(code, registry) for code in codes]`.

---

`first_unknown` loops over the codes and returns the first one whose lookup gives `False`.
