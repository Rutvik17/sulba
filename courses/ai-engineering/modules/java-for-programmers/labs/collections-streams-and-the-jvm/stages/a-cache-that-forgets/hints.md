`new LinkedHashMap<>(16, 0.75f, true)` keeps its entries in the order they were last used, with the one used least lately first.

---

A `LinkedHashMap` asks its `removeEldestEntry(eldest)` method after each `put` whether to drop its oldest entry. An anonymous subclass, `new LinkedHashMap<>(16, 0.75f, true) { @Override protected boolean removeEldestEntry(Map.Entry<K, V> eldest) { ... } }`, can answer.

---

Inside the anonymous class, `Recent.this.capacity` is the cache's own field.
