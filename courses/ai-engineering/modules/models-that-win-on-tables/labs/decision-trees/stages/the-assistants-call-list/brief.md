The call list was written by an assistant: `call_list.py`, whose `fit` grows a tree on the training calls and cuts it at the depth that ranks the validation calls best, and whose `call_list` puts tomorrow's clients in the order to call them, the likeliest first. Its four tests all pass.

Review it as if the list went out tomorrow: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way it will be used. A run shows how many pass. You see which ones when you finish the review.

What the call list must do:

- rank clients by what the bank knows before it calls them;
- choose the depth by the validation calls;
- keep at least {% $fig.min_leaf %} training calls in every leaf;
- rank a client in a category the training calls never had, with 0 in every column of that category.
