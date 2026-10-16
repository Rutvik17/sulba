A run of a text covers some letters when it holds each of them at least as many times as they appear. Write `smallest_cover`:

```
smallest_cover(text, letters) -> the shortest run of adjacent characters in text that covers
    letters, or "" if no run does
```

`smallest_cover("banana bread", "brad")` returns `"bread"`, and `smallest_cover("figure eight", "ight")` returns `"ight"`. When several runs tie for the shortest, return the one that starts first. `letters` holds at least one character, and every character counts, spaces included.

The tests' longest text has {% $fig.characters %} characters.
