Before you started, the help desk asked an assistant for everything the desk needs on a host. The assistant wrote `desk_ops.py`, its logs, readiness and server settings in one module, with `create()` and `config()` as your `main.py` has them. Its five tests all pass.

Review it as if the desk were about to ship with it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way a host will run it. A run shows how many pass, and you see which ones when you finish the review.

What the code must do:

- keep the logs free of what a request's address can hold;
- check the model without taking its time from callers;
- answer `/ready` in time, whatever hangs;
- take requests from the host's proxy.
