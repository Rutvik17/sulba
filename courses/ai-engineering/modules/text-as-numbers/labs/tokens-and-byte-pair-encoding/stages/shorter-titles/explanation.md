```python
def shorten(title, limit, ranks):
    pieces = regex.findall(PATTERN, title)
    kept, used = [], 0
    for piece in pieces:
        used += len(encode(piece, ranks))
        if used > limit:
            break
        kept.append(piece)
    else:
        return title
    if kept:
        return "".join(kept)
    first = pieces[0]
    for end in range(len(first), 0, -1):
        if len(encode(first[:end], ranks)) <= limit:
            return first[:end]
    return ""
```

A title's tokens are its pieces' tokens, one piece after another, because no token crosses from one piece into the next. So whole pieces can be counted one at a time, and the count only grows as pieces are added. Inside a piece it needn't: {% $fig.shorter %} takes {% $fig.shorter_tokens %} tokens, and {% $fig.longer %} takes {% $fig.longer_tokens %}, because one more character lets merges join what they couldn't before. Trying every length from the longest down finds the longest start that fits.

At a limit of {% $fig.limit %} tokens, {% $fig.us_cut %} of the {% $fig.us_titles %} US test titles are cut, keeping {% $fig.us_kept %} of their characters on average; {% $fig.es_cut %} of the {% $fig.es_titles %} Spanish titles, keeping {% $fig.es_kept %}; and {% $fig.jp_cut %} of the {% $fig.jp_titles %} Japanese titles, keeping {% $fig.jp_kept %}. {% $fig.jp_inside %} of the Japanese titles begin with a run of characters, without a space, longer than the limit, and are cut inside it. The same limit buys the most of a title in the language the tokenizer learnt from.
