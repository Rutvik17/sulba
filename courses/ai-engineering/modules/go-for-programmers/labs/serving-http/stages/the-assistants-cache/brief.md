The help desk's callers ask the same few questions again and again, and each one costs an upstream a reply. Before you started, the help desk asked an assistant for a cache in front of an upstream. The assistant wrote `cache.go`, with `NewCache`, and its four tests all pass.

Review it as if the gateway were about to put it in front of every upstream: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the gateway will use it. A run shows how many pass, and you see which ones when you finish the review.

What the code must do:

- ask its upstream again once a reply's time to live is up;
- let different requests reach its upstream at once;
- ask its upstream again after a failure;
- keep apart conversations that end with the same message.
