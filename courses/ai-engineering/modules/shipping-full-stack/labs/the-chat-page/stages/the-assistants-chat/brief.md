Before you started, the help desk asked an assistant for the page's chat. The assistant wrote `desk_chat.ts`, its own `Chat`, on your `api.ts` and `stream.ts`, for the page your `chat.ts` works with. It shows the desk's replies with their formatting, and its five tests all pass.

Review it as if the help desk were about to put it on the page: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the page will use it. A run shows how many pass, and you see which ones when you finish the review.

What the code must do:

- put nothing a reply holds on the page as markup;
- keep the status for what goes wrong, so a screen reader hears the reply once;
- let the caller send again after a reply fails;
- stop the reply's request at once when the chat closes.
