`Routes` is a map with methods of its own: Go lets a type you name have methods, a map's included. A map value refers to its entries, so `For` and `Models` take the map itself, not a pointer to it.

A map that was never made is nil, and the spec says what that means: "A nil map is equivalent to an empty map except that no elements may be added." Reading one gives the zero value, so `For` on nil routes finds no route, as it should. Writing is another matter: "Assigning to an element of a nil map causes a run-time panic." `ParseRoutes` makes its map with `Routes{}` before it adds to it. The two-result form, `upstreams, found := r[model]`, tells a model with no route from one whose list is empty.

A slice is a view of an array, and Go's blog on slices says what that means for sharing one: "Slicing does not copy the slice's data", and "modifying the elements (not the slice itself) of a re-slice modifies the elements of the original slice". Handing out the routes' own slice would let any caller change a model's upstreams for every request after it, so `For` gives each caller a copy with `slices.Clone`.

A map has no order. The spec: "The iteration order over maps is not specified and is not guaranteed to be the same from one iteration to the next", and `maps.Keys` says the same of its iterator. `slices.Sorted(maps.Keys(r))` collects the models and sorts them, so `Models` gives the same list every time.

`strings.Cut` splits a line at its first colon and says whether it found one, which is the check a line without a colon needs. Each `*LineError` keeps its line number, so a mistake in a long routes file points to the line that has it.
