```python
def common_prefix(words):
    if not words:
        return ""
    shortest = min(words, key=len)
    for position, character in enumerate(shortest):
        if any(word[position] != character for word in words):
            return shortest[:position]
    return shortest
```

The prefix ends at the first position where the words differ, or at the end of the shortest word, so the loop goes through the shortest word's characters and checks each against every word. It reads each word only up to the end of the prefix, so with `n` words and a prefix of `m` characters it takes time in proportion to `n` times `m`, besides finding the shortest word. Going through `shortest` keeps `word[position]` inside every word, and an empty word makes `shortest` empty, so the loop never runs and the answer is `""`.

Another way: the first and last words in sorted order share exactly the prefix that all the words share, so comparing just those two, `min(words)` and `max(words)`, gives the same answer.
