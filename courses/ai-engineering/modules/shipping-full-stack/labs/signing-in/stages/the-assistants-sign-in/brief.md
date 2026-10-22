Before you started, the help desk asked an assistant for the desk's sign-in routes. The assistant wrote `desk_auth.py`, on your `sign_in.py`, `tokens.py` and `sessions.py`. Its five tests all pass.

Review it as if the help desk were about to put it in front of its callers: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the help desk will use it. A run shows how many pass, and you see which ones when you finish the review.

What the code must do:

- send a person back, once they've signed in, only to a page of this site;
- give each sign-in a session no one could have known before it;
- sign each person in to their own account, and no one else's;
- end a session for good when its person signs out.

```
GET /auth/sign-in?back=/
GET /auth/callback
POST /auth/sign-out
```
