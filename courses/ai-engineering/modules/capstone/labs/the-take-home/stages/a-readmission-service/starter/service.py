from fastapi import FastAPI


def stays(path):
    """Each patient's first encounter in the extract at path, without those that ended in death
    or in hospice care, with readmitted True for a readmission within 30 days."""
    raise NotImplementedError


def train(table):
    """A scikit-learn model fitted to the stays in table, whose predict_proba takes rows like
    table's, without readmitted."""
    raise NotImplementedError


app = FastAPI()
