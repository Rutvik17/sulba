A cache keeps at most `capacity` keys. When it's full and a new key comes, it drops the key used longest ago. Write `Cache`:

```
Cache(capacity)
cache.get(key) -> the key's value, or -1 if the cache doesn't hold it
cache.put(key, value) -> None: sets the key's value, dropping the least recently used key
    first if the key is new and the cache is full
```

Both `get` and `put` use a key, so each makes it the most recently used, and `get` of a key the cache doesn't hold uses nothing. With a capacity of 2: `put(1, 1)`, `put(2, 2)`, `get(1)` gives 1, `put(3, 3)` drops key 2, so `get(2)` gives -1.

The tests' longest case puts and gets {% $fig.operations %} times with a capacity of {% $fig.capacity %}.
