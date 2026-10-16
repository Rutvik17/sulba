```python
def encode(text, ranks):
    return [
        rank
        for piece in regex.findall(PATTERN, text)
        for rank in encode_piece(piece, ranks)
    ]


def encode_piece(piece, ranks):
    tokens = [bytes([byte]) for byte in piece.encode()]
    while len(tokens) > 1:
        pairs = [
            (ranks.get(a + b), i) for i, (a, b) in enumerate(zip(tokens, tokens[1:]))
        ]
        known = [pair for pair in pairs if pair[0] is not None]
        if not known:
            break
        _, i = min(known)
        tokens[i : i + 2] = [tokens[i] + tokens[i + 1]]
    return [ranks[token] for token in tokens]


def decode(tokens, ranks):
    by_rank = {rank: token for token, rank in ranks.items()}
    return b"".join(by_rank[rank] for rank in tokens).decode(errors="replace")
```

The pair whose token has the lowest rank is the merge training made first, so encoding makes it first again, and a piece comes out in the tokens training would have left it in. Encoding works piece by piece, as training did: no merge crosses from one piece into the next.

Every title decodes back to itself. The encoding starts from bytes, so it loses nothing, and any text can be encoded, in any language. What a token holds can be part of a character, though. The commonest character in the Japanese titles, {% $fig.character %}, is the {% $fig.character_length %} bytes {% $fig.character_bytes %}, and no merge of the shop's joins them, so it takes {% $fig.character_tokens %} tokens. Of the {% $fig.cuts %} places where the tokens of the {% $fig.japanese %} Japanese titles could be cut, {% $fig.inside %}, {% $fig.inside_share %}, fall inside a character, and the tokens before such a cut decode to text that ends in U+FFFD. Decoding all the bytes together reads each character whole once its last byte is there.
