Before you started, the help desk asked an assistant for a way to answer sooner when an upstream is slow: ask every upstream at once, and take the first reply. The assistant wrote `fanout.go`, with `Fanout`, and its four tests all pass.

Review it as if the gateway were about to send every request through it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the gateway will use it. A run shows how many pass, and you see which ones when you finish the review.

What the code must do:

- leave no goroutine waiting once every upstream has answered;
- cancel the upstreams it no longer needs;
- wait past an upstream that fails for one that replies;
- give up at the caller's deadline, whatever the upstreams do.
