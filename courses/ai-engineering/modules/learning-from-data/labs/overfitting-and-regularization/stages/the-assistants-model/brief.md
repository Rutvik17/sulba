The plant asked an assistant to put your model into production with scikit-learn, and the assistant wrote `strength.py`. Its three tests all pass.

Review it as if the plant were about to rely on it: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way the plant will use it, against the model you built in stages 1 to 3. A run shows how many pass. You see which ones when you finish the review.

The plant's request:

- Choose the degree and penalty on the validation mixes, as you did.
- Fit the same model you validated.
- From our records, say how far off it will be on mixes we haven't made yet.
