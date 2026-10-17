The service answers over HTTP. Build it in `app.py` with FastAPI, around the model `train.py` saved:

- `GET /health` answers `{"status": "ok"}`.
- `POST /predict` takes a stay's fields, as the take-home's requests carried them, and answers with `probability`, the stay's chance of a readmission within 30 days, and `call`, `true` if that chance is at or above the saved threshold.

Write the request as `Stay` and the answer as `Prediction`, both pydantic models, and give `predict` the return type `Prediction`. FastAPI reads each request into a `Stay` before `predict` runs, and answers a 422 for one that doesn't fit. A stay must have every field, each a value the model can answer for:

| Field | Values |
| --- | --- |
| `age` | A band in `Age` |
| `gender` | `Female`, `Male` or `Unknown/Invalid` |
| `admission_type_id`, `admission_source_id`, `discharge_disposition_id` | A code in `AdmissionType`, `AdmissionSource` and `Discharge`: the ID mapping's, less the deaths and hospice care |
| `time_in_hospital` | {% $fig.shortest %} to {% $fig.longest %} days, as every stay in the extract is |
| The other counts | 0 or more |
| `A1Cresult` | `None`, `Norm`, `>7` or `>8` |
| `insulin` | `No`, `Down`, `Steady` or `Up` |
| `change` | `No` or `Ch` |
| `diabetesMed` | `No` or `Yes` |

Load the saved model with `load()` once, as `app.py` is imported, not for each request. The tests save a model trained on part of the extract before they import `app.py`, and send their requests in process.
