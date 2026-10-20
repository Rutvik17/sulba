`to_tsvector('english', body)` reads a passage into lexemes. Postgres's parser splits the text into tokens, and its English configuration lowercases each word, leaves it out if it is a stop word, one of the commonest words such as `the`, `can` and `not`, and cuts it to its stem with the Snowball stemmer, so that `Applying` and `apply` are both `appli`. Each lexeme keeps the places it was found, which ranking reads.

Postgres makes a generated column virtual unless it says `STORED`: worked out each time it's read, and impossible to index. Stored, a passage's words are worked out once, when the passage is written. A GIN index keeps, for each lexeme, the passages that hold it, and Postgres's documentation calls it the preferred index for text search. It finds the passages a query matches; ranking them reads each one's words.

`websearch_to_tsquery` reads a question as a search box would: its words joined by AND, `or` between two words making an OR, and a `-` before a word leaving out the passages that hold it. A question in full has words that few passages hold all of: of the {% $fig.questions %} validation questions, {% $fig.none %} found no passage that holds every one. A question made only of stop words, such as `What is it?`, leaves an empty query, which matches nothing.

Joined by OR, the questions find passages again. The hit rate at {% $fig.k %} is the share of questions with a passage that answers them among the first {% $fig.k %} found:

| Search | Hit rate at {% $fig.k %} | Hit rate at {% $fig.more %} |
| --- | --- | --- |
| Any word, by `ts_rank_cd` | {% $fig.any %} | {% $fig.any_more %} |
| The vectors | {% $fig.vectors %} | {% $fig.vectors_more %} |

`ts_rank_cd` ranks by how many times the query's words appear in a passage: for words joined by OR, {% $fig.weight %} for each. It doesn't weigh a word by how many passages hold it, as Postgres's documentation says its ranking functions "do not use any global information", so a passage that holds `benefit` twice ranks above one that holds `appeal` once, though {% $fig.benefit_held %} of the passages hold `benefit` and {% $fig.appeal_held %} hold `appeal`. The next stage weighs each word by how rare it is.
