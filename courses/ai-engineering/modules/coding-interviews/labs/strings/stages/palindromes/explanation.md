```python
def is_palindrome(text):
    left, right = 0, len(text) - 1
    while left < right:
        if not text[left].isalnum():
            left += 1
        elif not text[right].isalnum():
            right -= 1
        elif text[left].lower() != text[right].lower():
            return False
        else:
            left, right = left + 1, right - 1
    return True
```

Two positions move in from the ends, each stepping past characters that aren't letters or digits, and the letters and digits they stop at must match, ignoring case. Each step moves a position, so the loop takes time in proportion to the text, and it needs no space besides the two positions. The loop stops when they meet, so a text with no letters or digits gives `True`.

Keeping the letters and digits in a new string and comparing it with its reverse takes the same time but space in proportion to the text. Cutting a character off each end with `text[1:-1]` at each step copies the text every time: for the longest test's {% $fig.characters %} characters, that's {% $fig.copied %} characters copied. Copying is fast enough for that to fit the time limit, but the work grows with the square of the text's length.
