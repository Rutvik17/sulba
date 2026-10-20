The help desk asked an assistant for the report it will choose its searches by. The assistant wrote `report.py`: `scores`, each question's hit rate at {% $fig.k %} and nDCG at {% $fig.depth %}, judged by text; and `report`, each search's means over the questions and in each service, and each search's gain in hit rate over the current one, with the gain's p-value. Its four tests all pass.

Review it as if the help desk were about to choose its search by it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the help desk will use it, on its test questions. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- count every question judged, one a search shows nothing for as 0;
- see the passages as a reader does, each at its rank, a text shown before as `None`;
- judge nDCG by the answers' texts;
- test a gain question by question, swapping each question's two values where `rng.integers(0, 2, size=(REPEATS, len(a)))` gives 1.
