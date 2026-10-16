def is_palindrome(text):
    """Whether text's letters and digits read the same both ways, ignoring case."""
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
