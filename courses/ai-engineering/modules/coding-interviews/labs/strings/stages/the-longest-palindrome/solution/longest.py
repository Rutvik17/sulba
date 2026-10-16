def longest_palindrome(text):
    """The longest run of adjacent characters in text that reads the same both ways."""
    best = ""
    for center in range(len(text)):
        for left, right in ((center, center), (center, center + 1)):
            while left >= 0 and right < len(text) and text[left] == text[right]:
                left, right = left - 1, right + 1
            if right - left - 1 > len(best):
                best = text[left + 1 : right]
    return best
