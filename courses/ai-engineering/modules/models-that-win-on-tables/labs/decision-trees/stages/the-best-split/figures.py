import pandas as pd
from sklearn.tree import DecisionTreeClassifier

# The smallest side the explanation's splits keep.
MIN_LEAF = 25
NUMBERS = ["pdays", "previous", "age", "campaign"]


def figures():
    table = pd.read_csv("data/calls.csv")
    train = table[table["set"] == 0]
    said_yes = (train["subscribed"] == "yes").to_numpy()
    share = said_yes.mean()
    found = {
        "calls": f"{len(table):,}",
        "share": f"{(table['subscribed'] == 'yes').mean():.1%}",
        "train": f"{len(train):,}",
        "yes": f"{said_yes.sum():,}",
        "root": f"{2 * share * (1 - share):.3f}",
        "min_leaf": str(MIN_LEAF),
    }
    for name in NUMBERS:
        column = train[name].to_numpy(dtype=float)
        stump = DecisionTreeClassifier(max_depth=1, min_samples_leaf=MIN_LEAF)
        nodes = stump.fit(column[:, None], said_yes).tree_
        counts, impurities = nodes.n_node_samples, nodes.impurity
        threshold = nodes.threshold[0]
        left = column <= threshold
        found[f"{name}_t"] = f"{threshold:g}"
        found[f"{name}_left"] = f"{left.sum():,} calls, {said_yes[left].mean():.1%} yes"
        found[f"{name}_right"] = (
            f"{(~left).sum():,} calls, {said_yes[~left].mean():.1%} yes"
        )
        impurity = (counts[1] * impurities[1] + counts[2] * impurities[2]) / counts[0]
        found[f"{name}_g"] = f"{impurity:.3f}"
    # The explanation lists the columns from the least impurity left to the most.
    impurities = [float(found[f"{name}_g"]) for name in NUMBERS]
    assert impurities == sorted(impurities)
    never = train["pdays"] == 999
    found["never"] = f"{never.mean():.1%}"
    return found
