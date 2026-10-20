The help desk's passages came from one way of cutting its pages: each page's blocks, its headings, paragraphs and list items, joined in order until another would take a passage past 200 words. This lab measures what that choice costs, and what other ways would. A page can't go to the model whole: the lab's model server embeds at most {% $fig.context %} tokens of a text, and refuses a longer one, and the longest of the {% $fig.pages %} pages has {% $fig.longest %} words.

`data/pages.csv` holds each page's text, its blocks a blank line apart. In `chunk.py`, write:

- `words(text)`: each word's place in the text, a word being a run of characters other than space: its first character and the one after its last.
- `windows(text, size, overlap)`: the text cut into windows of `size` words, each starting `size - overlap` words after the one before, the last ending at the text's last word. A window runs from its first word's first character to the one after its last word's last. Raise `ValueError` unless `overlap` is at least 0 and less than `size`.
- `blocks(text)`: the place of each block, lines with no blank line between them.
- `joined(text, most)`: the blocks joined in order until another would take a chunk past `most` words, each chunk from its first block's first character to the one after its last block's last. A block of more than `most` words is a chunk of its own.

```
words(text) -> list of (start, end)
windows(text, size, overlap=0) -> list of (start, end)
blocks(text) -> list of (start, end)
joined(text, most) -> list of (start, end)
```
