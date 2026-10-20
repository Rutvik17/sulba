A sentence added to one block of each of the {% $fig.pages %} pages sends these chunks to be embedded again:

| Chunks | Embedded again | A page | Answer parts kept whole |
| --- | --- | --- | --- |
| Windows of 100 words | {% $fig.windows_again %} | {% $fig.windows_per_page %} | {% $fig.windows_whole %} |
| Blocks joined to 100 words | {% $fig.joined_again %} | {% $fig.joined_per_page %} | {% $fig.joined_whole %} |
| Blocks joined, a heading starting each chunk | {% $fig.desk_again %} | {% $fig.desk_per_page %} | {% $fig.desk_whole %} |

Answer parts kept whole counts those of the {% $fig.parts %} parts of the test questions' answers that lie within one chunk. A window starts a set number of words after the one before, so a sentence added to a page moves every window after it, and each of them is embedded again. Joined blocks change from the edited block until a chunk starts at the same block it did before. A heading that starts a chunk stops the change at the end of its section, and every page has a chunk that changes, so the fewest an edit can send is one a page.

The help desk keeps each vector under its chunk's text, as a cache keyed by the text does, so a chunk that comes back with the same text isn't embedded again. Its place moves when an edit comes before it, so the places come from the chunker each time, and only the vectors are kept.
