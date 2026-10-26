Before you started, the office asked an assistant for the desk's API too. The assistant wrote `desk_api.py`, all in one module, with a log of the questions asked and a way for the office's staff to look a student up. Its three tests all pass.

Review it as if the office were about to serve it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the office's chat page will call it, with the college's sign-in and the office's database. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- give a student only their own aid;
- answer a visitor's question for staff with the message asking them to sign in;
- keep students' questions out of the log;
- end every answer with its verdict.
