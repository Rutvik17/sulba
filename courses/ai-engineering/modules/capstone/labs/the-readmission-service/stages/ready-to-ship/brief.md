Before the service ships, the team needs to see which model is answering and how its calls are going, and to know it answers in time. Add to `app.py`:

```
GET /model -> {"threshold": ..., "recall": ..., "precision": ..., "versions": {...}}
GET /stats -> {"answered": ..., "called": ...}
```

`/model` describes the model answering: the threshold, recall and precision `train` set, and the versions it was trained with, as `Model`. `/stats` counts, as `Stats`, the stays the service has answered since it started, through `/predict` and `/predict/batch`, and how many of them it called. A batch the service refuses counts for nothing.

The threshold was set to call `SHARE` of the stays. Called over answered is the share the service is calling now, and if it drifts far from `SHARE`, something has changed: the patients, the way their stays are coded, or the model. Three checks decide whether it ships. There are no hints. The tests are hidden: you see which pass, but not their inputs.
