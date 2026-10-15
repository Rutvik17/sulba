For element `i`, make an array of zeros with a 1 at `i`. Then `lambda t: f(x + t * axis)` is `f` along that element alone, and your `central_difference` of it at 0 is the slope you need.

---

The length of a vector is `np.sqrt(np.sum(v**2))`. Divide the length of `a - b` by the larger of the two lengths, after checking that it isn't 0.
