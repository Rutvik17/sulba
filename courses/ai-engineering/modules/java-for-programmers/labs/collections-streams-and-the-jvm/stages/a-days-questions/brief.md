The desk keeps a log of every question it answers, and the benefits office reads reports from it each day. This lab builds the desk's reports and memory in Java, with its collections and streams. The lab gives you `Service.java` again.

In `Reports.java`, the starter gives you the records: `Asked(at, service, page, reply)`, one question, asked at an `Instant` about a service from a help page, whose reply took a `Duration`; and `PageCount(page, questions)`. Write four reports, each from a log of questions:

- `byService(log)` counts each service's questions, in the order `Service` declares the services. A service with no questions isn't in it.
- `topPages(log, n)` gives the `n` pages with the most questions, most first. Pages with as many come in the order of their names. `n` of 0 gives none, and less than 0 is an `IllegalArgumentException`.
- `medianReply(log)` gives how long the median reply took: the middle reply's time, or with an even number, the mean of the middle two. An empty log has none.
- `byHour(log, zone)` counts the questions in each hour of the day, from 0 to 23, on the clock of the zone, in order of the hour. An hour with no questions isn't in it.

None of them changes the log it's given.

```java
public static Map<Service, Long> byService(List<Asked> log)
public static List<PageCount> topPages(List<Asked> log, int n)
public static Optional<Duration> medianReply(List<Asked> log)
public static SortedMap<Integer, Long> byHour(List<Asked> log, ZoneId zone)
```

The office is in New York, and the tests' log is from Monday 2 November 2026.
