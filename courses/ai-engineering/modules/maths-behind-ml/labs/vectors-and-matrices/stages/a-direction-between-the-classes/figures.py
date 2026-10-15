import numpy as np

PATH = "data/breast-cancer.csv"


def figures():
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    with open(PATH) as file:
        names = [
            name.replace("_", " ") for name in file.readline().strip().split(",")[2:]
        ]
    new = table[:, 0] == 1
    X, y = table[~new, 2:], table[~new, 1]
    mean, std = X.mean(axis=0), X.std(axis=0)
    Z, Zn, own = (X - mean) / std, (table[new, 2:] - mean) / std, table[new, 1]
    mu0, mu1 = Z[y == 0].mean(axis=0), Z[y == 1].mean(axis=0)
    u = (mu1 - mu0) / np.linalg.norm(mu1 - mu0)
    score = (Zn - (mu0 + mu1) / 2) @ u
    malignant = own == 1
    heaviest, lightest = int(np.argmax(np.abs(u))), int(np.argmin(np.abs(u)))
    right = int(np.sum((score > 0) == malignant))
    return {
        "new": str(len(own)),
        "measurements": str(Z.shape[1]),
        "malignant": str(int(malignant.sum())),
        "malignant_right": str(int(np.sum(score[malignant] > 0))),
        "benign": str(int((~malignant).sum())),
        "benign_right": str(int(np.sum(score[~malignant] < 0))),
        "right": str(right),
        "right_share": f"{right / len(own):.1%}",
        "apart": f"{np.linalg.norm(mu1 - mu0):.2f}",
        "heaviest_name": names[heaviest],
        "heaviest": f"{abs(u[heaviest]):.3f}",
        "lightest_name": names[lightest],
        "lightest": f"{abs(u[lightest]):.4f}",
    }
