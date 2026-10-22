Before you started, the help desk asked an assistant for the desk's replies. The assistant wrote `desk_replies.py`, its own version of the reply route, on your conversations and your gate. Its four tests all pass.

Review it as if the help desk were about to use it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the help desk will use it. A run shows how many pass, and you see which ones when you finish the review.

What the code must do:

- take no place at the gate for a message it can't answer;
- give its place back however a reply ends;
- keep one agent for each conversation, for as long as the conversation lasts;
- end every reply at the gate's time limit.
