The help desk asked an assistant for the test set it will measure each release on, and the report of a release's pass rate. The assistant wrote `evalset.py`: `held_out`, the test set's questions, and `report`, a release's pass rate on them with its margin of error at 95%. Its four tests all pass.

Review it as if the help desk were about to measure its next release with it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the help desk will use it, on its questions. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- leave out each question with the same words as an earlier one;
- move each page whole, so that no page has questions on both sides;
- give each service its share of its own questions;
- give the same test set for the same seed, run after run;
- count each page's questions together in the margin of error.
