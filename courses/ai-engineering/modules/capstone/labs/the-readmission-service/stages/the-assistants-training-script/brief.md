The team asked an assistant for the script that trains the service's model, and the assistant wrote `train.py`. Its four tests all pass.

Review it as if the service were about to load what it trains: fix every problem you can find, and keep what it does right. Three hidden production checks test it the way the service and the planners will use it. A run shows how many pass. You see which ones when you finish the review.

The team's request:

- Fit the model chosen in stage 5 on the extract's stays.
- Set the threshold that calls the planners' share of the stays, `SHARE`.
- Say what recall and precision the planners can expect at that threshold, on patients the model has never seen.
