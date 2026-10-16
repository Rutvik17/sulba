One pass with a dict: at each position, look up `target - number` among the numbers before it, then add the number. A lookup takes constant time on average, so the pass takes time in proportion to the list's length, and the dict as much space.

Trying every pair takes `$n(n-1)/2$` comparisons, which grows with the square of the length and runs past the time limit on the longest list.
