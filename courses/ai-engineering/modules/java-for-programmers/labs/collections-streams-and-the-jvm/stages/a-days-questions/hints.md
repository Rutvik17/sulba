`Collectors.groupingBy(Asked::service, () -> new EnumMap<>(Service.class), Collectors.counting())` counts by service into an `EnumMap`, which keeps the enum's order. `TreeMap::new` in that place gives a map in order of its keys.

---

`Comparator.comparingLong(PageCount::questions).reversed().thenComparing(PageCount::page)` puts the most first and breaks ties by name. `reversed()` turns around the comparator it's called on, so where it sits matters.

---

`stream.sorted()` gives a sorted stream and leaves the list behind it alone. `a.plus(b).dividedBy(2)` is the mean of two `Duration`s.

---

`asked.at().atZone(zone).getHour()` gives the hour on the zone's clock that day.
