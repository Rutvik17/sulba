The desk's service keeps each conversation's agent in memory between a caller's messages, so it needn't read the conversation back for every one. A service that kept every conversation it had ever seen would fill its memory, so it keeps the ones used most lately, and forgets the one used least lately to make room, as Python's `functools.lru_cache` does.

In `Recent.java`, write `Recent<K, V>`, made with how many values it holds, which is at least 1: fewer is an `IllegalArgumentException`.

- `get(key)` gives the key's value, if the cache holds it, and counts as a use of it. A key it doesn't hold changes nothing.
- `put(key, value)` holds the value by its key, in place of any value it held before, and counts as a use. Holding one more than it has room for forgets the value used least lately.
- `remove(key)` forgets the key's value, and gives it, if the cache held it.
- `keys()` gives the keys it holds, the one used least lately first, as a list that later changes to the cache don't change.
- `size()` gives how many values it holds.

A key or value that's `null` is a `NullPointerException`.

```java
public Recent(int capacity)
public Optional<V> get(K key)
public void put(K key, V value)
public Optional<V> remove(K key)
public List<K> keys()
public int size()
```
