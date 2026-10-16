`titles.assign(characters=..., tokens=...)` adds a column of each title's characters, `titles["title"].str.len()`, and one of its tokens from your `encode`.

---

`groupby("shop")[["characters", "tokens"]].sum()` adds up each shop's columns, and dividing one column by the other gives characters per token.
