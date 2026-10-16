```python
def costs(titles, ranks):
    counted = titles.assign(
        characters=titles["title"].str.len(),
        tokens=[len(encode(title, ranks)) for title in titles["title"]],
    )
    totals = counted.groupby("shop")[["characters", "tokens"]].sum()
    return totals.assign(per_token=totals["characters"] / totals["tokens"])
```

Characters per token is the ratio of the totals, so a long title counts for more than a short one, as it does in the shop's total. Over the {% $fig.per_shop %} test titles from each shop:

| Shop | Characters a title | Tokens a title | Characters a token |
| --- | --- | --- | --- |
| US | {% $fig.us_characters %} | {% $fig.us_tokens %} | {% $fig.us_per %} |
| Spain | {% $fig.es_characters %} | {% $fig.es_tokens %} | {% $fig.es_per %} |
| Japan | {% $fig.jp_characters %} | {% $fig.jp_tokens %} | {% $fig.jp_per %} |

A Spanish title shares the US titles' alphabet but not their words: {% $fig.us_seen %} of a US test title's pieces occur in the training titles, and {% $fig.es_seen %} of a Spanish one's. The merges fit it less well, so it takes more tokens for its length. A Japanese title has about half the characters of a US one and takes {% $fig.jp_ratio %} times its tokens: {% $fig.jp_per_character %} tokens a character. {% $fig.jp_three_bytes %} of its characters take three bytes, and merges learnt from English join few of them. The chart shows it: with no merges a token is a byte, and the merges that make English titles shorter leave Japanese ones almost where they began.

The `qwen` column counts the same titles with the tokenizer of Qwen2.5, an open model made for many languages, Spanish and Japanese among them. It is a byte-pair encoding too, with a far larger vocabulary learnt from far more text. A US title takes {% $fig.us_qwen %} of its tokens, {% $fig.us_qwen_per %} characters a token; a Spanish one {% $fig.es_qwen %}, {% $fig.es_qwen_per %} a token; and a Japanese one {% $fig.jp_qwen %}, {% $fig.jp_qwen_per %} a token. The gap narrows, and a Japanese title still costs {% $fig.jp_qwen_ratio %} times a US one's tokens with half its characters. What a text costs is a property of the tokenizer as much as of the text: count it with the tokenizer of the model that will read it.
