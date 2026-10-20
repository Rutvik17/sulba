Each problem passed the assistant's tests because each test checked something beside it. The model in the tests embedded a question the same way after either prefix, its vectors were made so that a slice cut them as the card does, three ids sorted the way they came, and asking for one passage hid the order of the rest.

The prefix is part of what the model reads, and the card asks for `search_query: ` before a question because a question and its answer are different kinds of text. A wrong prefix raises no error: the search still finds passages, just fewer of the right ones.

A slice is one of the card's steps, not all of them. A vector's first numbers are shorter than the whole vector, by more for some passages than for others, and a dot product grows with both vectors' lengths as well as with how closely they point the same way. Scaled to a length of 1, as `shorten` does, the cut vectors are scored by their direction alone.

Ids and vectors kept apart must stay in the same order. Keeping one list of ids beside the rows they label, made from the same dictionary in the same order, is what `list(passages)` does.

`np.argsort` sorts from the lowest. A search keeps the highest scores, so it sorts the negated scores, and `kind="stable"` keeps the passage that comes first in front where two scores tie, as two passages with the same text do.
