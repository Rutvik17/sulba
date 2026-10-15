The line's code was written by an assistant: `line.py`, whose `sort_batch` names the beans of each batch that comes down the line, and whose `estimated_accuracy` tells the company how often it names a bean right. Its four tests all pass.

Review it as if the line were about to start: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way it will be used. A run shows how many pass. You see which ones when you finish the review.

What the line must do:

- name each bean the same way whatever else its batch holds, scaled by the training beans' statistics;
- estimate its accuracy with each training bean named by the others;
- give a tied vote to the variety of the nearest of the tied neighbours;
- send back as `None` a bean the camera measured only in part.
