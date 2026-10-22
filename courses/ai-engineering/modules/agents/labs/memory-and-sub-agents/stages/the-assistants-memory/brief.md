The help desk asked an assistant for the desk's memory before you started. The assistant wrote `desk_memory.py`, whose `DeskMemory` keeps the agent's conversation within a budget of tokens, with the notes the model saves and a summary of the turns it no longer holds. Its four tests all pass.

Review it as if the help desk were about to use it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the help desk will use it. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- clear the oldest tool results first, and keep the most recent;
- count each request's prompt and reply against the budget;
- summarise whole turns, so that every tool result it keeps has its call;
- keep the notes in every request, summarised or not.
