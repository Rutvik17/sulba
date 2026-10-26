`routes := Routes{}` makes a map you can add to. `var routes Routes` is nil, and adding to it panics.

---

`strings.Cut(line, ":")` gives the text before and after the first colon, and whether there was one. `strings.Split(list, ",")` and `strings.TrimSpace` do the rest of a line.

---

`slices.Clone(upstreams)` copies a slice, and `slices.Sorted(maps.Keys(r))` gives a map's keys sorted.
