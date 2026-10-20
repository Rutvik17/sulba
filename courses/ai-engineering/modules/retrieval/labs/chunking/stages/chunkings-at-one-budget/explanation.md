Each chunking was searched with the {% $fig.questions %} validation questions at {% $fig.budget %} words, each search taking the chunks most similar to its question until the next would take it past the budget:

| Chunks | Found | Recall | IoU |
| --- | --- | --- | --- |
| Windows of 100 words | {% $fig.words_100_found %} | {% $fig.words_100_recall %} | {% $fig.words_100_iou %} |
| Blocks joined to 100 words | {% $fig.blocks_100_found %} | {% $fig.blocks_100_recall %} | {% $fig.blocks_100_iou %} |
| Windows of 200 words | {% $fig.words_200_found %} | {% $fig.words_200_recall %} | {% $fig.words_200_iou %} |
| Windows of 200 words sharing 50 | {% $fig.words_200_50_found %} | {% $fig.words_200_50_recall %} | {% $fig.words_200_50_iou %} |
| Blocks joined to 200 words, the passages | {% $fig.blocks_200_found %} | {% $fig.blocks_200_recall %} | {% $fig.blocks_200_iou %} |
| Windows of 400 words | {% $fig.words_400_found %} | {% $fig.words_400_recall %} | {% $fig.words_400_iou %} |

Found is how many chunks a search takes on average. The chunkings of 100 words find the most of each answer: a search through them takes twice as many chunks as one through those of 200 words, each holding less of its page. Windows that share words find about what windows of the same size that share none find, though they take more words to embed and keep. At {% $fig.larger %} words the gap narrows: windows of 100 words find {% $fig.words_100_larger %} of an answer on average, and the passages {% $fig.blocks_200_larger %}.
