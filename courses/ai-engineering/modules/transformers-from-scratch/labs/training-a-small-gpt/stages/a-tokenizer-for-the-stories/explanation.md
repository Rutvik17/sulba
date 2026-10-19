A vocabulary of {% $fig.size %} tokens takes {% $fig.merges %} merges, and the separator is token {% $fig.end %}. The stories and their separators, {% $fig.text_bytes %} bytes, come to {% $fig.tokens %} tokens: {% $fig.bytes_2048 %} bytes a token, and {% $fig.per_story %} tokens a story on average.

The vocabulary's size is a trade. Each token is a row of the token embedding, which in a GPT is the output layer too, so its numbers grow with the vocabulary, while each doubling makes the tokens only a little longer:

| Vocabulary | Bytes a token | Embedding at width {% $fig.width %} |
| --- | --- | --- |
| {% $fig.vocab_512 %} | {% $fig.bytes_512 %} | {% $fig.embedding_512 %} |
| {% $fig.vocab_1024 %} | {% $fig.bytes_1024 %} | {% $fig.embedding_1024 %} |
| {% $fig.vocab_2048 %} | {% $fig.bytes_2048 %} | {% $fig.embedding_2048 %} |
| {% $fig.vocab_4096 %} | {% $fig.bytes_4096 %} | {% $fig.embedding_4096 %} |

Longer tokens let a context of the same length hold more of a story, and make each story fewer steps to write. GPT-2's vocabulary of {% $fig.gpt2 %} tokens is made for text of every kind. These stories use few words, and the app's model is small, so a vocabulary of {% $fig.size %} keeps its embedding to {% $fig.embedding_2048 %} numbers.

The stories split into {% $fig.pieces %} pieces, and only {% $fig.distinct %} of them are different, so training counts each distinct piece once and weighs it by how often it appears. Counting every pair again for each merge reads {% $fig.recounted %} pairs over the {% $fig.merges %} merges. Keeping the counts, and updating only the pieces a merge changes, touches {% $fig.touched %}: {% $fig.fewer %} times fewer. Both learn the same merges.

The separator is one token, so the model can learn where a story ends and the app can stop on it. GPT-3 trained the same way: its documents were packed into sequences one after another, with an end-of-text token between them, so the model could learn that what follows one isn't part of what came before.
