A comparison with a missing value gives a missing value: Spark's page on null semantics says "Normal comparison operators return `NULL` when one of the operand is `NULL`." Left alone, a trip with no drop-off time would be neither `backwards` nor not, `~` of its flag would be missing too, and `clean` with it. `coalesce`, which "Returns the first column that is not null", turns each missing flag into false, so every trip is flagged or not.

`greatest` of the flags is true when any of them is, and "It will return null if all parameters are null", which can't happen once each flag has been coalesced. `count_if` "Returns the number of TRUE values for the col", so one `agg` can count every flag at once.

| Flag | Trips |
| --- | --- |
| `outside_month` | {% $fig.outside_month %} |
| `backwards` | {% $fig.backwards %} |
| `too_long` | {% $fig.too_long %} |
| `no_distance` | {% $fig.no_distance %} |
| `negative` | {% $fig.negative %} |
| `unknown_zone` | {% $fig.unknown_zone %} |
| clean | {% $fig.clean %} |

A trip can break more than one rule, so the flags add up to more than the {% $fig.flagged %} trips that aren't clean.
