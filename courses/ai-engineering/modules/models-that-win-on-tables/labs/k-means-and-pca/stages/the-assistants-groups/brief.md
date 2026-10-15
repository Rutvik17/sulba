The report on the new supplier's harvest was written by an assistant: `report.py`, whose `run` finds the two directions for the inspectors' plot, groups the training beans with k-means, names each group by its commonest variety, and names each bean of the harvest by the group it falls into. Its four tests all pass.

Review it as if the harvest were sorted tomorrow: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way it will be used. A run shows how many pass. You see which ones when you finish the review.

What the report must do:

- plot the beans along the two directions in which they vary most;
- group the beans by their scaled measurements;
- name each group by the variety most of its own training beans have;
- put each harvest bean in the training group whose centre is nearest it.
