import pandas as pd

PATH = "data/encounters.csv"


def figures():
    text = pd.read_csv(PATH, dtype=str, keep_default_na=False)
    defaults = pd.read_csv(PATH)
    shares = (text == "?").mean()
    return {
        "encounters": f"{len(text):,}",
        "patients": f"{text['patient_nbr'].nunique():,}",
        "columns": str(text.shape[1]),
        "a1c_lost": f"{defaults['A1Cresult'].isna().sum():,}",
        "glucose_lost": f"{defaults['max_glu_serum'].isna().sum():,}",
        "weight": f"{shares['weight']:.1%}",
        "specialty": f"{shares['medical_specialty']:.1%}",
        "payer": f"{shares['payer_code']:.1%}",
        "race": f"{shares['race']:.1%}",
        "diag_3": f"{shares['diag_3']:.1%}",
        "diag_2": f"{shares['diag_2']:.1%}",
    }
