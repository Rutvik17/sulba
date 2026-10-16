Keep a window with no repeats, and grow it one character at a time. When the new character is already in the window, where must the window start now?

---

Keep each character's last position in a dict. When the new character's last position is inside the window, start the window just after it.
