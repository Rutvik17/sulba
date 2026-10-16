The assistant's tests used three short English titles, none of them spelling out a special token, a limit that ends right after a separator, and a reply in ASCII. None counted a title in another language, planted the separator's text in a title, tried a limit that ends inside the next title, or streamed a character split across tokens.

---

Each problem treated tokens as if they were text: a token is no fixed number of characters, a special token isn't text a seller can write, every token in a prompt counts toward its limit, separators too, and a token's bytes can be part of a character.
