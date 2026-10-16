```python
def longest_palindrome(text):
    best = ""
    for center in range(len(text)):
        for left, right in ((center, center), (center, center + 1)):
            while left >= 0 and right < len(text) and text[left] == text[right]:
                left, right = left - 1, right + 1
            if right - left - 1 > len(best):
                best = text[left + 1 : right]
    return best
```

Each position is the middle of an odd palindrome, and the gap after it the middle of an even one. From each middle, the loop widens the run while the characters on both sides match, and keeps the longest run found. Middles come in order, and only a longer run replaces `best`, so of runs that tie, the one that starts first stays.

In the worst case, a text of one character repeated, each middle widens all the way, so the time grows with the square of the text's length, with no extra space. On most texts, widening stops after a few characters. Checking every run instead, each against its reverse, takes time that grows with the cube of the length. A table of which runs are palindromes, filled from short runs to long, takes the square of the length in both time and space.
