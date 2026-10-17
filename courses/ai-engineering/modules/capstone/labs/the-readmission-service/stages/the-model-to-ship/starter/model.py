from sklearn.ensemble import HistGradientBoostingClassifier


def make_boosted():
    """Boosted trees: 50 trees of depth 3 at a learning rate of 0.1, on the counts and age as
    they are and the categories one-hot encoded."""
    encode = ColumnTransformer(
        [
            ("numbers", "passthrough", [*COUNTS, "age"]),
            (
                "categories",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORIES,
            ),
        ]
    )
    trees = HistGradientBoostingClassifier(
        max_iter=50, max_depth=3, learning_rate=0.1, random_state=SEED
    )
    return make_pipeline(encode, trees)


def make_weighted():
    """The logistic regression with the readmitted stays weighted up, as class_weight="balanced"
    does: together they weigh as much as the stays not readmitted."""
    encode = ColumnTransformer(
        [
            ("numbers", StandardScaler(), [*COUNTS, "age"]),
            ("categories", OneHotEncoder(handle_unknown="ignore"), CATEGORIES),
        ]
    )
    return make_pipeline(
        encode, LogisticRegression(max_iter=1000, class_weight="balanced")
    )


def make_chosen():
    """A new, unfitted pipeline of the model to ship."""
    raise NotImplementedError


def chosen(table):
    """The model to ship, fitted to every stay in table."""
    raise NotImplementedError
