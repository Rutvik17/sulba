Each morning the planners' system leaves the day's discharges in a file, written as the extract is. The assistant wrote `call_list.py`, which turns that file into the day's call list with your service. Its three tests all pass.

Review it as if the planners were about to call from its list: fix every problem you can find, and keep what it does right. Three hidden production checks run it against your service on days like the ones it will meet. A run shows how many pass. You see which ones when you finish the review.

The planners' request:

- Score every discharge of the day with the service, in batches of up to its limit.
- Leave out the deaths and hospice care, who aren't called.
- List each stay's encounter, probability and call, most likely to come back first.
