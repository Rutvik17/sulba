Count what `letters` needs, and grow a window until it covers them. Then shrink the window from its start for as long as it still covers them.

---

Keep how many characters are still missing. A character joining the window lowers it only if the window still needed that character, and a character leaving raises it only if the window then needs one more.
