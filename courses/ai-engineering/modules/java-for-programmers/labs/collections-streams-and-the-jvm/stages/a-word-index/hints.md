`Pattern.compile("\\w+", Pattern.UNICODE_CHARACTER_CLASS)` matches a run of word characters in any script, and `matcher(text).results()` gives a stream of the matches.

---

`text.toLowerCase(Locale.ROOT)` lowercases a text the same way on every computer.

---

`passages.computeIfAbsent(word, key -> new TreeSet<>()).add(id)` adds an id to a word's set, making the set first if the word is new. `Collections.unmodifiableSortedSet(set)` gives a view of it that can't change it.

---

`shared.merge(id, 1, Integer::sum)` counts a passage once more, starting from 1. A `LinkedHashSet` of the query's words keeps each word once.
