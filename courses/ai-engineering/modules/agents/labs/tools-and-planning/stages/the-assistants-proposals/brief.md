The help desk asked an assistant for the desk's proposals before you started. The assistant wrote `desk_actions.py`, whose `Actions` proposes tickets and callbacks for the model, and makes them when the caller says yes. Its three tests all pass.

Review it as if the help desk were about to use it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the help desk will use it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- make nothing before the caller says yes;
- drop a proposal when the caller's next message doesn't say yes;
- check the time again on a yes, and make nothing it can't finish;
- ask which ticket a call is about when the caller has more than one open for the service.
