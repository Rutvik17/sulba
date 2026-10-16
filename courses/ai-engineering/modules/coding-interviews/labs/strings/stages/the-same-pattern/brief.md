Two texts follow the same pattern when renaming the first's characters turns it into the second, each character always renamed to the same one and no two characters to the same one. Write `same_pattern`:

```
same_pattern(first, second) -> whether first and second follow the same pattern
```

`same_pattern("paper", "title")` returns `True`: `p` becomes `t`, `a` becomes `i`, `e` becomes `l` and `r` becomes `e`. `same_pattern("ab", "aa")` and `same_pattern("aa", "ab")` both return `False`, and texts of different lengths never follow the same pattern.

The tests' longest texts have {% $fig.characters %} characters each, every one different.
