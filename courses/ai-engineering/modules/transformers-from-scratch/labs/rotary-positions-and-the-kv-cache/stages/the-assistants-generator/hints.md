Call `positions(5, 2)`: the two new tokens follow five cached ones.

---

Compare `torch.arange(3).repeat(3)` with `torch.arange(3).repeat_interleave(3)`, and work out which key head query head 1 reads in each.

---

Print `allowed(4, 1)`, one new token after four cached ones, and count the tokens it reads.

---

Look at which row of the prompt's logits picks the story's first token.
