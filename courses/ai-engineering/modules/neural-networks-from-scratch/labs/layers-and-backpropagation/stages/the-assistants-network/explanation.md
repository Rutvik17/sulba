The assistant's tests each took the smallest case: one digit, one layer, logits near 0 and a single backward pass. Each of those hides a problem. With one digit, a sum and a mean are the same. With one layer, the forward order and the reverse are the same. Near 0, `np.exp` can't overflow. And after one backward pass, a gradient added to zeros is the gradient.

---

Training is the opposite of each: batches of digits, through every layer, step after step, toward logits that grow as the network grows sure. Code is checked the way it will run, and here that means against PyTorch's results for batches and deeper networks, at confident logits, and over more than one step.
