`math.floor(share * 1000) / 10` is a share's low end in percent, rounded down to a tenth; `math.ceil` rounds the high end up.

---

`payback` gives `math.inf` for months that never come. Test the estimate and the high end with `math.isinf` before writing them.
