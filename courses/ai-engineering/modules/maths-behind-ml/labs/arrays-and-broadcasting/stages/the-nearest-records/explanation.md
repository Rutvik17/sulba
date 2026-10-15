`np.argsort(D, axis=1, kind="stable")` sorts each of the {% $fig.new %} rows on its own and returns, for each, the record numbers in order of distance. Only a stable sort promises that equal distances keep their order. The default, quicksort, isn't stable: it promises no order for them, and a search should give the same records every time it's asked.

Sorting a whole row to keep its first `k` does more work than it needs. `np.argpartition` finds the `k` smallest without sorting the rest, but it leaves those `k` in no promised order, so they must still be sorted after it.

Indexing with an array of positions builds an array of the same shape. `near` has the shape ({% $fig.new %}, `$k$`), so `diagnoses[near]` does too, and averaging along axis 1 gives each new sample its share of malignant records.

With `$k$` = {% $fig.k %}, {% $fig.malignant_mostly %} of the {% $fig.malignant %} malignant new samples have mostly malignant records nearest them, and {% $fig.benign_mostly %} of the {% $fig.benign %} benign ones mostly benign records. On average, a malignant sample's nearest records are {% $fig.malignant_mean %} malignant and a benign sample's {% $fig.benign_mean %}. Over all the new samples, {% $fig.same %} of the nearest records share the sample's diagnosis, against {% $fig.raw_same %} on the raw measurements.

A share is a description of the records found, not a diagnosis. It says what the most similar past samples turned out to be, as measured by these {% $fig.k %} distances.
