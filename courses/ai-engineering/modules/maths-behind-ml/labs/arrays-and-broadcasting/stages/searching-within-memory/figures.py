import numpy as np

# The checks' sizes: new samples looked up at once, records, and the memory allowed.
LOOKUPS, RECORDS, BUDGET = 50, 10_000, 32_000_000
BYTES = 8


def figures():
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    new = table[:, 0] == 1
    d = table.shape[1] - 2
    per_row = RECORDS * d * BYTES
    naive_rows = BUDGET // per_row
    rows = BUDGET // (4 * per_row)
    return {
        "lookups": str(LOOKUPS),
        "big_records": f"{RECORDS:,}",
        "measurements": str(d),
        "new": str(int(new.sum())),
        "records": str(int((~new).sum())),
        "budget_mb": f"{BUDGET / 1e6:.0f}",
        "full_mb": f"{LOOKUPS * per_row / 1e6:.0f}",
        "naive_rows": str(naive_rows),
        "naive_mb": f"{naive_rows * per_row / 1e6:.1f}",
        "rows": str(rows),
        "chunk_mb": f"{rows * per_row / 1e6:.1f}",
        "records_mb": f"{per_row / 1e6:.1f}",
    }
