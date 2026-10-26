Before you started, the help desk asked an assistant for the gateway's usage counter. The assistant wrote `usage.go`: it counts each key's tokens by day, refuses tokens over a day's limit, merges the counts another of the gateway's servers kept, and saves its counts to a file and reads them back. Its seven tests all pass.

Review it as if the gateway were about to charge keys with it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the gateway will use it. A run shows how many pass, and you see which ones when you finish the review.

What the code must do:

- merge the counts of keys this server has never seen;
- keep its keys in the order they were first seen, whatever a caller does with them;
- charge a batch of uses past one that's over the limit, and count that one as refused;
- give an error for a file it can't read.
