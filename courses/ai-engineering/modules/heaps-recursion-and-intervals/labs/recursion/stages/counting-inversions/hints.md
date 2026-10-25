Split the list into halves. An inversion is inside the left half, inside the right, or across them. Which can you count while merging the halves once they're sorted?

---

Sort each half by calling the function on it, counting its inversions as it goes. While merging, a number taken from the right half is smaller than every number still waiting in the left half: that many inversions cross the halves.
