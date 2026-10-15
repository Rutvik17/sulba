`clean_chunks` keeps one table across the chunks: the earliest encounter so far of each patient. `pd.concat([firsts, chunk])` joins a chunk to it, and `first_encounters` keeps the earlier of each patient's encounter so far and the chunk's. The table never holds more than one row per patient, and each chunk can go once it's folded in.

```python
def clean_chunks(chunks):
    firsts = None
    for chunk in chunks:
        firsts = first_encounters(
            chunk if firsts is None else pd.concat([firsts, chunk])
        )
    return drop_deaths_and_hospice(mark_unknown(firsts))
```

The earliest of all the encounters is the earliest of each chunk's earliest, so finding it works chunk by chunk. Leaving out deaths and hospice care doesn't: a patient whose first encounter ended in hospice care is left out altogether, and whether an encounter is a patient's first is known only once every chunk has been read. Done chunk by chunk, it counts such a patient at a later encounter. Marking codes for unknown looks at one row at a time, so it can be done anywhere.

The tests give `read_csv` each column's type because, without `dtype`, it works out each chunk's types from that chunk's rows alone. `payer_code` is missing from the extract's first {% $fig.no_payer %} encounters, so in the first chunks it would read as numbers, all of them missing. In chunks of {% $fig.small %}, one chunk's `diag_1` codes all look like numbers, so it would read code {% $fig.code %} as {% $fig.code_float %}, which no longer equals the text "{% $fig.code %}" in every other chunk. A pipeline that reads in chunks gives every column its type.
