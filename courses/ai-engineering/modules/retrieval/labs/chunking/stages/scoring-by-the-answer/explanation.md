Scored by the characters of its answer, a search through one chunking can be compared with a search through any other, on the same questions. Recall is the share of the answer that reaches the model, precision the share of what reaches it that's the answer, and IoU, the intersection over the union, falls when either does.

An answer is short: the {% $fig.questions %} validation questions' answers have {% $fig.answer %} characters on average. A search that finds exactly the chunks that hold part of an answer brings the rest of each chunk too, so the larger the chunks, the lower its precision. Each chunking's chunks, and the precision of those that hold a validation question's answer, on average:

| Chunks | Characters a chunk | Precision |
| --- | --- | --- |
| Single blocks | {% $fig.blocks_size %} | {% $fig.blocks %} |
| Blocks joined to 100 words | {% $fig.blocks_100_size %} | {% $fig.blocks_100 %} |
| Blocks joined to 200 words, the passages | {% $fig.blocks_200_size %} | {% $fig.blocks_200 %} |
| Windows of 100 words | {% $fig.words_100_size %} | {% $fig.words_100 %} |
| Windows of 200 words | {% $fig.words_200_size %} | {% $fig.words_200 %} |
| Windows of 400 words | {% $fig.words_400_size %} | {% $fig.words_400 %} |
| Windows of 200 words sharing 50 | {% $fig.words_200_50_size %} | {% $fig.words_200_50 %} |

An answer in the words two windows share is held by both, and precision counts the characters of each: the chunks that hold a validation question's answer number {% $fig.shared_chunks %} on average for windows of 200 words sharing 50, and {% $fig.plain_chunks %} for windows of 200 that share none.
