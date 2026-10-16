The assistant's tests made one enums, gave a message only to a string, never counted a failure, and never used a union once it was joined into another.

---

In a JavaScript class body, `options = []` is a field, made again for each instance. In a Python class body, it's one list, held by the class, and `self.options.extend(...)` added every enums' options to it. A class attribute suits a value no instance changes in place, such as `message = None`, and that one hid the second problem: Python runs only the `__init__` it finds first, so `Enums.__init__` ran in place of `Struct`'s, and `self.message` found the class's `None`. JavaScript makes a subclass's constructor call `super()` before it uses `this`. Python leaves the call to the subclass.

A dataclass that compares by its fields and isn't frozen gets no hash, since changing a field would change its place in a dict, and a `Counter` is a dict, keyed by what it counts. `|` gives a new object for sets and dicts, and the service's structs need the same: a union joined into another is still the struct of its own field.
