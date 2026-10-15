import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler

# The neighbours each validation bean is sorted by.
K = 15


def figures():
    table = pd.read_csv("data/beans.csv")
    # Every column after the set and the variety is a measurement.
    measurements = list(table.columns[2:])
    train, validation = table[table["set"] == 0], table[table["set"] == 1]
    a, b = train[measurements].to_numpy(), validation[measurements].to_numpy()
    sd = a.std(axis=0)
    # Between two beans picked at random, a measurement's expected squared difference is twice
    # its variance, so its share of the squared distance is its share of the total variance.
    variance = sd**2
    areas = [measurements.index("Area"), measurements.index("ConvexArea")]
    share = variance[areas].sum() / variance.sum()

    def accuracy(train_rows, validation_rows):
        model = KNeighborsClassifier(n_neighbors=K, algorithm="brute")
        model.fit(train_rows, train["variety"])
        return (model.predict(validation_rows) == validation["variety"]).mean()

    scaler = StandardScaler().fit(a)
    return {
        "measurements": str(len(measurements)),
        "area_sd": f"{sd[measurements.index('Area')]:,.0f}",
        "solidity_sd": f"{sd[measurements.index('Solidity')]:.4f}",
        "share": f"{share:.3%}",
        "k": str(K),
        "unscaled": f"{accuracy(a, b):.1%}",
        "scaled": f"{accuracy(scaler.transform(a), scaler.transform(b)):.1%}",
    }
