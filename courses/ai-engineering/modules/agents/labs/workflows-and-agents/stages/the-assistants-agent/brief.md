The help desk asked an assistant for its agent before you started. The assistant wrote `desk_agent.py`, whose `DeskAgent` sends the caller's messages to the model with the desk's tools, runs the tools the model calls, and replies. Its three tests all pass.

Review it as if the help desk were about to use it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the help desk will use it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- end a turn after at most `ROUNDS` requests, with `OutOfRounds`;
- send each tool's result back after the model's message that called it;
- give the model an error to read for any call that can't run;
- keep the conversation from one of the caller's messages to the next.
