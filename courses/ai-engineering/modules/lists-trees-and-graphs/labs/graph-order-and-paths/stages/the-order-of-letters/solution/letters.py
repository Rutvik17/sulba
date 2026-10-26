from collections import deque


def letter_order(words):
    """The words' letters, each once, in an order of the alphabet that sorts the words as
    they're given, or an empty string if no order does."""
    letters = list(dict.fromkeys(letter for word in words for letter in word))
    after = {letter: set() for letter in letters}
    for first, second in zip(words, words[1:]):
        for a, b in zip(first, second):
            if a != b:
                after[a].add(b)
                break
        else:
            if len(first) > len(second):
                return ""
    waiting_on = dict.fromkeys(letters, 0)
    for followers in after.values():
        for letter in followers:
            waiting_on[letter] += 1
    ready = deque(letter for letter in letters if waiting_on[letter] == 0)
    order = []
    while ready:
        letter = ready.popleft()
        order.append(letter)
        for later in after[letter]:
            waiting_on[later] -= 1
            if waiting_on[later] == 0:
                ready.append(later)
    return "".join(order) if len(order) == len(letters) else ""
