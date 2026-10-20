`re.finditer(r"\n[^\S\n]*\n", text)` finds each blank line, one with nothing but spaces, tabs or a carriage return between two newlines. The blocks are what lies between them, from the first word to the end of the last.

---

Add a sentence to a block in the middle of a page, chunk the page again, and count the chunks whose text is new. Which chunks after the edit change, and where do the changes stop?

---

A heading starts a section of a page. A chunk that starts at each heading can't hold text from two sections, so an edit can't change a chunk of another section.
