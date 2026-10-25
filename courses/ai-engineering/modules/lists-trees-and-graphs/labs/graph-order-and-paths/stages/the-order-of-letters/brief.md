A language uses some of the 26 lower case letters, in an alphabetical order of its own, and `words` is a list of its words, sorted in its order, as a dictionary sorts them: by their first letter, then the words that share it by their second, and so on, a word before the longer words it begins. Write `letter_order`:

```
letter_order(words) -> every letter in the words, once, in an order that sorts the words as
    they're given, or "" if no order does
```

For `["wrt", "wrf", "er", "ett", "rftt"]`, the order is `"wertf"`. When the words leave some letters' order open, as `["ab", "cd"]` does for b and d, any order that sorts them will do, and the tests accept any. When no order can, such as for `["ab", "a"]` or `["a", "b", "a"]`, it's `""`. The tests' longest list has {% $fig.words %} words.
