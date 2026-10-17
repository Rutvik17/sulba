An AUC of {% $fig.model %} on {% $fig.test %} held-out stays says that, of a readmitted patient and one who wasn't, the model gives the readmitted one the higher probability in {% $fig.model_share %} of pairs. Whether that's worth a service depends on what the planners have without it.

They have the record of each patient's year. {% $fig.none_before %} of the held-out stays had no inpatient visit in the year before, and {% $fig.rate_none %} of those were readmitted, against {% $fig.rate_some %} of the stays that had one or more. Ranked by that count alone, the stays score an AUC of {% $fig.baseline %}, with nothing to train and nothing to serve. A random order scores 0.5.

So the model's lead is {% $fig.model %} against {% $fig.baseline %}: real, but no larger than that. The baseline is also the floor every later choice is held to. A change that loses that lead isn't worth making, however good its other numbers.

The held-out stays have to stay out of everything the model learns. `scores` fits the whole pipeline, scaler and encoder included, on the stays it learns from, so even the counts' means and spreads come from them alone. Stratifying the split keeps the readmitted share the same in both parts, {% $fig.rate %} here, so the test isn't easier or harder by the luck of the draw.

One split is still one draw. The {% $fig.test %} held-out stays hold {% $fig.readmitted %} readmissions, and a different draw would give a different AUC. Stage 3 measures how different.
