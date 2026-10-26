`call(name, arguments)` has a `Tool<?>`, whose record type is unknown. A private generic method, `<A extends Record> String call(Tool<A> tool, String arguments)`, gives that type a name, `A`, inside it.

---

`JsonMapper`'s `readTree(text)` gives a `JsonNode`: `isObject()`, `propertyNames()`, `has(key)` and `get(key)` say what the model wrote. `treeToValue(node, tool.arguments())` then reads it into the record.

---

`tool.arguments().getRecordComponents()` gives the record's components, in order, and each one's `getName()`.

---

A `DatabindException`'s `getPath()` gives where in the JSON it went wrong: the first reference's `getPropertyName()` is the key. A `ValueInstantiationException`, one kind of `DatabindException`, is the one a constructor caused, with that exception as its cause, so catch it first.
