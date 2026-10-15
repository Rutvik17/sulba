The checks score the model on the test mixes, which played no part in fitting it or in choosing it. It accepts {% $fig.accepted %} of their {% $fig.test_tests %} tests:

| Test set | Tests | RMSE |
| --- | --- | --- |
| Accepted | {% $fig.accepted %} | {% $fig.accepted_rmse %} MPa |
| Refused | {% $fig.refused %} | {% $fig.refused_rmse %} MPa |
| All | {% $fig.test_tests %} | {% $fig.all_rmse %} MPa |

The refused tests come from {% $fig.refused_mixes %} mixes. One has {% $fig.coarse %} kg of coarse aggregate, where no training mix has more than {% $fig.coarse_top %} kg, and the other has {% $fig.fine %} kg of fine aggregate, where none has more than {% $fig.fine_top %} kg. For them, the model extends a polynomial of degree 3 past the mixes it was fit on, and its strengths miss by up to {% $fig.worst %} MPa.

Checking each measurement against its range is a first guard, not a complete one. The ranges are taken one measurement at a time, so a mix can sit inside all eight and still combine them in a way no training mix comes near.

The test mixes are used once, after the choice, for the error the plant is told: {% $fig.accepted_rmse %} MPa on the mixes the model accepts. The validation error of the chosen pair, {% $fig.val_rmse %} MPa, was the lowest of the {% $fig.tries %} pairs tried, and a pair can come out lowest in part by suiting those particular mixes. So the validation error of the chosen model tends to understate its error on new mixes.
