The extract stores each encounter's admission type, discharge and admission source as numbers, and `data/ids-mapping.csv` says what each number means. Some of them mean that no answer was recorded: the mapping describes them as NULL, Not Available, Not Mapped or Unknown/Invalid.

| Column | Codes for unknown |
| --- | --- |
| `admission_type_id` | {% $fig.admission_codes %} |
| `discharge_disposition_id` | {% $fig.discharge_codes %} |
| `admission_source_id` | {% $fig.source_codes %} |

`gender` writes `Unknown/Invalid` for no answer too. Write `mark_unknown`, a copy of the table with each of these read as missing, and `drop_sparse`, a copy without the columns whose share of missing values is over `limit`.

```
mark_unknown(table) -> a DataFrame, the code columns still whole numbers
drop_sparse(table, limit) -> a DataFrame, without the sparse columns
```

Neither changes the table it's given. The tests mark the extract that `read_encounters` reads.
