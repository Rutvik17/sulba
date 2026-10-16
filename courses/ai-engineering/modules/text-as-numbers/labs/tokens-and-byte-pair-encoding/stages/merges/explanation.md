```python
def train(texts, merges):
    counts = Counter(piece for text in texts for piece in regex.findall(PATTERN, text))
    pieces = {piece: [bytes([byte]) for byte in piece.encode()] for piece in counts}
    ranks = {bytes([byte]): byte for byte in range(256)}
    for _ in range(merges):
        pairs = Counter()
        for piece, tokens in pieces.items():
            for pair in zip(tokens, tokens[1:]):
                pairs[pair] += counts[piece]
        if not pairs:
            break
        first, second = max(pairs, key=pairs.__getitem__)
        ranks[first + second] = len(ranks)
        for piece, tokens in pieces.items():
            pieces[piece] = merge(tokens, first, second)
    return ranks


def merge(tokens, first, second):
    joined, i = [], 0
    while i < len(tokens):
        if i + 1 < len(tokens) and tokens[i] == first and tokens[i + 1] == second:
            joined.append(first + second)
            i += 2
        else:
            joined.append(tokens[i])
            i += 1
    return joined
```

The {% $fig.titles %} training titles split into {% $fig.pieces %} pieces, but only {% $fig.distinct %} distinct ones, so counting each distinct piece once and weighting its pairs by its count saves most of the work of each merge.

The first merges join {% $fig.first_merges %}: a space and S occurs {% $fig.first_count %} times, once for each word after a space that begins with S. The {% $fig.tie_at %} merge is a tie: {% $fig.tie_first %}, and {% $fig.tie_second %}, each occur {% $fig.tie_count %} times. The first of them occurs first in the titles, so it merges first, and the other right after. A trainer that broke ties another way would learn other ranks, and encode some text into other tokens, so a tokenizer's rule for ties is part of what it is.

After all {% $fig.merges %} merges, the training titles' {% $fig.bytes %} bytes take {% $fig.tokens %} tokens, {% $fig.per_token %} bytes a token. The longest tokens, {% $fig.longest %}, are {% $fig.longest_bytes %} bytes each with the space before them: whole words, frequent enough in the titles to earn a token of their own.
