The service's records go through an assistant's port of superstruct's walk, `walker.py`. `failures` walks a record, `problems` explains its failures for the form, and `first_failures` takes the first failures of a day's records. Its five tests all pass.

Review it as if the service were about to check a day's records with it: fix every problem you can find, and keep what it does right. Four hidden production checks test it the way the service will use it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- find failures at any depth, inside arrays as well as objects;
- reject a value that isn't the object its schema asks for;
- explain every failure of a record, the first one too;
- read no record past the failures `first_failures` gives.
