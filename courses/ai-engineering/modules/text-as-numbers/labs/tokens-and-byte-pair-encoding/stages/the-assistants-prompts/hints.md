Try each function on a Japanese title from `data/titles.csv`: compare `count` with `len(encoding.encode_ordinary(title))`, and the last text `stream` gives with the title.

---

What does `encoding.encode` make of a title that spells out `<|endoftext|>` when `allowed_special` is `"all"`? And what does `used` leave out?
