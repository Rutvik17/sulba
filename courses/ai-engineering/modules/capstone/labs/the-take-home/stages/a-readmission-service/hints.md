`read_csv` with `na_values=["?"]` and `keep_default_na=False` reads `?` as missing and keeps `None` as written. `sort_values("encounter_id")`, then `drop_duplicates("patient_nbr")`, keeps each patient's first encounter, and `~isin(codes)` on `discharge_disposition_id` leaves out the deaths and hospice care.

---

A pipeline keeps the encoding with the model. `make_pipeline` takes a `ColumnTransformer`, which scales the counts with `StandardScaler` and one-hot encodes the other fields with `OneHotEncoder(handle_unknown="ignore")`, then a `LogisticRegression`. The `ColumnTransformer` picks its columns by name, so `predict_proba` takes the table's rows as they are.

---

A pydantic model with a field for each of the request's, typed `int` or `str`, makes FastAPI answer a 422 for a request that doesn't fit it. In `/predict`, `pd.DataFrame([stay.model_dump()])` turns the request into a row for `predict_proba`.
