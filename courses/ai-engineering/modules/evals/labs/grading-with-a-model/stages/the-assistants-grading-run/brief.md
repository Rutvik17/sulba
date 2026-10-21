The help desk asked an assistant for the code that grades its replies with Granite Guardian, and the threshold to call them by. The assistant wrote `judge.py`: `graded`, the grader's risk for each item, a context and a reply; `chosen`, the threshold BEGIN gives; `agreement`, the grader's kappa with people on BEGIN's test set at a threshold; and `flagged`, the share of replies a threshold calls ungrounded. Its four tests all pass.

Review it as if the help desk were about to grade every reply of its next release with it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the help desk will use it, on its replies and on BEGIN's. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- grade each reply with the context it comes with, asking only once for an item that repeats one before it;
- show the grader the whole context;
- stop when the server refuses a request;
- choose the threshold on BEGIN's development set, so that its kappa on the test set is measured on replies it never saw.
