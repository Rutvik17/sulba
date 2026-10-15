import pandas as pd

PATH = "data/encounters.csv"
OPTIONS = {"na_values": ["?"], "keep_default_na": False}
# The chunk size the tests read the extract in, and a smaller one, at which a chunk reads diag_1
# as numbers. The memory check's chunks of the extract's first rows, how many, and how many
# chunks' rows it allows; and the speed check's copies of the whole extract.
CHUNK, SMALL = 1000, 250
HELD_ROWS, HELD_COPIES, HELD = 2000, 6, 3
COPIES = 10


def figures():
    table = pd.read_csv(PATH, **OPTIONS)
    payer = table["payer_code"].notna().to_numpy()
    misread = next(
        chunk["diag_1"]
        for chunk in pd.read_csv(PATH, chunksize=SMALL, **OPTIONS)
        if chunk["diag_1"].dtype == "float64"
    )
    code = misread.dropna().iloc[0]
    return {
        "chunk": f"{CHUNK:,}",
        "encounters": f"{len(table):,}",
        "copies": str(COPIES),
        "big": f"{COPIES * len(table):,}",
        "held_rows": f"{HELD_ROWS:,}",
        "held_copies": str(HELD_COPIES),
        "held": f"{HELD * HELD_ROWS:,}",
        "held_chunks": str(HELD),
        "no_payer": f"{payer.argmax():,}",
        "small": str(SMALL),
        "code": f"{code:g}",
        "code_float": f"{code:.1f}",
    }
