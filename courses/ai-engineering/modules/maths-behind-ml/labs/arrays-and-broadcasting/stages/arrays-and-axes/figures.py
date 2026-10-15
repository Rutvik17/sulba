import numpy as np

PATH = "data/breast-cancer.csv"


def figures():
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    with open(PATH) as file:
        names = file.readline().strip().split(",")[2:]
    in_records = table[:, 0] == 0
    records, diagnoses = table[in_records, 2:], table[in_records, 1]
    new_diagnoses = table[~in_records, 1]
    std = records.std(axis=0)
    low, high = int(np.argmin(std)), int(np.argmax(std))
    n = len(records)
    return {
        "rows": str(table.shape[0]),
        "columns": str(table.shape[1]),
        "measurements": str(records.shape[1]),
        # Each measure comes three ways: its mean, its standard error and its worst value.
        "measures": str(
            len(
                {
                    name.removeprefix("mean_")
                    .removeprefix("worst_")
                    .removesuffix("_error")
                    for name in names
                }
            )
        ),
        "records": str(n),
        "records_malignant": str(int(diagnoses.sum())),
        "new": str(len(new_diagnoses)),
        "new_malignant": str(int(new_diagnoses.sum())),
        "low_name": names[low].replace("_", " "),
        "low_std": f"{std[low]:.4f}",
        "high_name": names[high].replace("_", " "),
        "high_std": f"{std[high]:.1f}",
        "ratio": f"{std[high] / std[low]:,.0f}",
        "n_minus_one": str(n - 1),
        # Dividing by n - 1 instead of n makes every standard deviation larger by this much.
        "ddof_larger": f"{np.sqrt(n / (n - 1)) - 1:.2%}",
    }
