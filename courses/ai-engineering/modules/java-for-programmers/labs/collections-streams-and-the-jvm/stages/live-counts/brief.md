The reports read a day's log once it's written. The office also wants its dashboard live: counts of the day's questions as they come in. The desk's Java service answers each request on a thread of its own, thousands at a time on a busy morning, and each records its question as it's answered, while the dashboard reads the counts.

In `Tally.java`, write `Tally`, which any number of threads use at once:

- `record(asked)` counts a question, from any thread.
- `total()` gives how many questions it has counted.
- `byService()` gives each service's count, in the order `Service` declares them, leaving out a service with none.
- `topPages(n)` gives the `n` pages with the most questions, as `PageCount`s, most first, and pages with as many in the order of their names, as `Reports.topPages` does.

Each report gives the counts as they stand when it's made: later questions don't change it, and it can't be changed.

```java
public void record(Reports.Asked asked)
public long total()
public Map<Service, Long> byService()
public List<Reports.PageCount> topPages(int n)
```

The tests show you which of their cases pass, but not what they gave or expected. Checks then test what the counts need before the dashboard goes live.
