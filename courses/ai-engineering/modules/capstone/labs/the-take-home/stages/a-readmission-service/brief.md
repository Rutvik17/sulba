The hospital network's discharge planners call some patients after they leave, to keep them from coming back. To choose whom to call, they want a service that gives, as a stay ends, the chance the patient is readmitted within {% $fig.days %} days. Build a first version in `service.py`.

The extract is `data/encounters.csv`: {% $fig.encounters %} encounters of {% $fig.patients %} patients. It marks a missing value `?`, and in `A1Cresult`, `None` is a test not done. Write:

```
stays(path) -> each patient's first encounter, as rows of the extract at path, without those
    that ended in death or in hospice care, and with readmitted True or False
train(table) -> a scikit-learn model fitted to the stays in table, whose predict_proba takes
    rows like table's, without readmitted
app -> a FastAPI app, serving a model trained on every stay
```

A patient's first encounter is the one with the lowest `encounter_id`. In `discharge_disposition_id`, codes {% $fig.death_codes %} are deaths, and {% $fig.hospice_codes %} hospice care. `readmitted` is `True` where the extract has `<30`, a readmission within {% $fig.days %} days.

`app` answers two requests:

- `GET /health` with `{"status": "ok"}`.
- `POST /predict` with `{"probability": p}`, that chance for the stay in the request. A request missing a field, or with a value its field can't take, such as `"a week"` for `time_in_hospital`, gets a 422.

A request for `/predict` carries a stay's fields, named and written as in the extract:

```json
{
  "age": "[70-80)",
  "gender": "Female",
  "admission_type_id": 1,
  "admission_source_id": 7,
  "discharge_disposition_id": 1,
  "time_in_hospital": 5,
  "num_lab_procedures": 44,
  "num_procedures": 1,
  "num_medications": 16,
  "number_outpatient": 0,
  "number_emergency": 0,
  "number_inpatient": 1,
  "number_diagnoses": 9,
  "A1Cresult": "None",
  "insulin": "Steady",
  "change": "No",
  "diabetesMed": "Yes"
}
```

| Field | What it holds |
| --- | --- |
| `age` | The patient's age band, such as `[70-80)` |
| `gender` | `Female`, `Male` or `Unknown/Invalid` |
| `admission_type_id`, `admission_source_id`, `discharge_disposition_id` | How the stay began and ended, as codes that `data/ids-mapping.csv` describes |
| `time_in_hospital` | The days from admission to discharge |
| `num_lab_procedures`, `num_procedures` | How many lab tests, and other procedures, the stay had |
| `num_medications` | How many distinct medicines, by generic name, were given |
| `number_outpatient`, `number_emergency`, `number_inpatient` | How many outpatient, emergency and inpatient visits the patient had in the year before |
| `number_diagnoses` | How many diagnoses were entered |
| `A1Cresult` | The HbA1c test's result: `>8`, `>7` or `Norm`, or `None` if it wasn't done |
| `insulin` | `Up`, `Down` or `Steady` for a dose raised, lowered or kept, or `No` if it wasn't prescribed |
| `change` | `Ch` if the diabetes medicines changed, or `No` |
| `diabetesMed` | `Yes` if any diabetes medicine was prescribed, or `No` |

The tests train your model on {% $fig.learn_share %} of the stays, chosen at random, and score it on the other {% $fig.held_out %} by AUC, which must be over {% $fig.floor %}.
