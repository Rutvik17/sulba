`[each for each in read("data/timings.csv") if each.release == name]` gives a release's own timings, and each one's `first` and `whole` go to `percentile` apart.

---

`f"{share:.0%}"` writes a share as a whole percent, `f"{seconds:.1f} s"` seconds to a tenth, and `f"{hourly:,.0f}"` a count with a comma for thousands.
