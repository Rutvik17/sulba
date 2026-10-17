import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DEATH_OR_HOSPICE = [11, 13, 14, 19, 20, 21]
COUNTS = [
    "time_in_hospital",
    "num_lab_procedures",
    "num_procedures",
    "num_medications",
    "number_outpatient",
    "number_emergency",
    "number_inpatient",
    "number_diagnoses",
]
CATEGORIES = [
    "gender",
    "admission_type_id",
    "admission_source_id",
    "discharge_disposition_id",
    "A1Cresult",
    "insulin",
    "change",
    "diabetesMed",
]


def inputs(rows):
    bands = rows["age"].str.extract(r"\[(\d+)-(\d+)\)").astype(int)
    out = rows[COUNTS].astype(int).assign(age=(bands[0] + bands[1]) / 2)
    return out.join(rows[CATEGORIES].astype(str))


# The request the brief shows.
STAY = {
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
    "diabetesMed": "Yes",
}


def figures():
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    first = table.sort_values("encounter_id").drop_duplicates("patient_nbr")
    kept = first[~first["discharge_disposition_id"].isin(DEATH_OR_HOSPICE)]
    y = (kept["readmitted"] == "<30").to_numpy()

    def model():
        encode = ColumnTransformer(
            [
                ("numbers", StandardScaler(), [*COUNTS, "age"]),
                ("categories", OneHotEncoder(handle_unknown="ignore"), CATEGORIES),
            ]
        )
        return make_pipeline(encode, LogisticRegression(max_iter=1000))

    folds = StratifiedKFold(5, shuffle=True, random_state=0)
    scored = cross_val_predict(
        model(), inputs(kept), y, cv=folds, method="predict_proba"
    )
    threshold = np.quantile(scored[:, 1], 0.9)
    fitted = model().fit(inputs(kept), y)
    probability = fitted.predict_proba(inputs(pd.DataFrame([STAY])))[0, 1]
    return {
        "probability": f"{probability:.3f}",
        "threshold": f"{threshold:.3f}",
        "call": "true" if probability >= threshold else "false",
        "longest": str(int(kept["time_in_hospital"].max())),
        "shortest": str(int(kept["time_in_hospital"].min())),
    }
