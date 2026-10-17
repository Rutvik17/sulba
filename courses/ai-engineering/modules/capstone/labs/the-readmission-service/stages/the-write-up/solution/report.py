"""The readmission service's write-up for the hospital network, with every number worked out
from the model and the stays."""

from sklearn.model_selection import StratifiedKFold

from model import SEED, auc, baseline, calibration, summary
from train import SHARE


def write_up(table, trained, probabilities):
    """The one-page write-up, in Markdown: for the stays in table, the model and threshold
    train gave, and each stay's out-of-fold probability."""
    y = table["readmitted"].to_numpy()
    folds = StratifiedKFold(5, shuffle=True, random_state=SEED).split(table, y)
    mean, error = summary(
        [auc(table.iloc[test], probabilities[test]) for _, test in folds]
    )
    predicted, observed = calibration(y, probabilities)
    return f"""# The readmission service

## What it answers

As each stay ends, the service gives the chance that the patient is readmitted within 30
days, and whether to call them. It learned from {len(y):,} stays, each patient's first in
the extract, and {y.mean():.1%} of them were readmitted.

## How well it ranks

Over five folds, each scored by a model that never saw its stays, the mean AUC is
{mean:.3f} ± {error:.3f}, give or take one standard error. Ranking the stays by their
inpatient visits in the year before alone gives {baseline(table):.3f}.

## How far its probabilities hold

On stays it never saw, its probabilities add up to {probabilities.sum():,.0f} readmissions,
and {int(y.sum()):,} came back. The tenth of stays it rates highest average
{predicted[-1]:.1%}, and {observed[-1]:.1%} of them were readmitted.

## The calls

It calls each stay with a probability of {trained["threshold"]:.3f} or more, the
{SHARE:.0%} of new stays most likely to come back. Of the readmissions, {trained["recall"]:.1%}
are among those called, and {trained["precision"]:.1%} of the calls reach a stay that comes
back.

## What it doesn't know

It learned from one in ten patients of 130 hospitals between 1999 and 2008, and from each
patient's first stay only. It doesn't answer for a stay that ended in death or hospice care,
or for one longer than 14 days. Its probabilities hold for patients like those; for others,
check the share called against the share planned before trusting it.
"""
