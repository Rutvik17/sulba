The desk's search finds help passages by their words, as Retrieval's BM25 did. Its first part is an index from each word to the passages that have it. In `Index.java`, write `Index`, made from each passage's text by the passage's id:

- `words(text)` gives a text's words, in order: its runs of letters, digits and underscores, lowercased, as Python's `re.findall(r"\w+", text.lower())` gives them. Letters outside ASCII are letters too, so `Café` gives `café`, and a computer set to any language lowercases them the same way.
- `passagesWith(word)` gives the ids of the passages that have the word, in order, as a set that can't be changed. A word no passage has gives an empty set.
- `find(query, k)` gives the `k` passages that have the most of the query's words, most first, as `Hit(passage, shared)` records. A word the query repeats counts once. Passages with as many come in the order of their ids, and a passage with none of the words isn't found.

```java
public Index(Map<String, String> texts)
public static List<String> words(String text)
public SortedSet<String> passagesWith(String word)
public List<Hit> find(String query, int k)
```

The tests index six passages from the four services' help pages, with the ids `p1` to `p6`.
