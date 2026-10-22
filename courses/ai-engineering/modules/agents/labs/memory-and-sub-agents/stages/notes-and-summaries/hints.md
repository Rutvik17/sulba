Each turn starts at a message whose role is `user`. With their indexes in `starts`, the last `turns` of them begin at `starts[-turns]`, and everything before it is summarised.

---

Write the summary's prompt from the turns you'll drop before you drop them, and keep the turns from the cut on: `self.messages[cut:]`.

---

`fit` calls `clear()` first, which gives 0 once everything older than the last `keep` results is cleared already.
