`pd.read_csv(path, na_values=["?"], keep_default_na=False)` reads each `?` as missing, and no other string. With `read_csv`'s defaults, every `?` would stay a string, and each `None` would turn into a missing value: {% $fig.a1c_lost %} A1C results and {% $fig.glucose_lost %} glucose results, every one a test not done. Whether a test was done is information in itself. Read as missing, those results would be mixed up with values the extract lost.

pandas reads a column of whole numbers as `int64` and a column of text as `str`. A missing value in a text column is `NaN`, and `isna()` finds a missing value in a column of any type. `mean()` counts `True` as 1 and `False` as 0, so the mean of `isna()` is the share missing:

| Column | Missing |
| --- | --- |
| `weight` | {% $fig.weight %} |
| `medical_specialty` | {% $fig.specialty %} |
| `payer_code` | {% $fig.payer %} |
| `race` | {% $fig.race %} |
| `diag_3` | {% $fig.diag_3 %} |
| `diag_2` | {% $fig.diag_2 %} |

Weight is missing from almost every encounter: in the years these records cover, US hospitals didn't have to record it in a structured form. The rest are missing often enough to need a decision, and the codes that stand for an unknown value, the next stage's work, aren't counted here at all.
