The page has a dashboard of the person's usage of the desk: for each of the last seven days, how many turns there were and how many were done, their tokens, what those would cost, and how long they took. The desk's `/usage` gives the days that had turns, oldest first, in UTC. In `dashboard.ts`, write:

- `usageTable(document, usage, days, now, prices)`, which makes the table, with `document`'s `createElement`:
  - a caption, such as `The desk's usage, last 7 days`;
  - a header row, `Day`, `Turns`, `Done`, `Prompt tokens`, `Reply tokens`, `Cost`, `Median`, `90th percentile`;
  - a row for each of the last `days` UTC days, today's by `now` included, the earliest first. A day the desk didn't give had no turns;
  - a total row, `Total`, with the days' turns, the share of them done, their tokens and their cost, and `—` for the median and the 90th percentile.
- Each number is formatted for `en-US` with `Intl`. A day is `Thu, Oct 22`, a count `1,234`, the share done a percentage such as `92%`, a time in seconds such as `1.2 sec`, to one decimal place, and a cost in dollars with two to four decimal places, such as `$0.0042`. With no turns, the share done and the times are `—`.
- A day's cost is its prompt tokens at `prices.prompt` and its reply tokens at `prices.completion`, each a price in dollars for a million tokens.
- `new Dashboard(desk, prices, elements)` and `dashboard.show(days, now)`, which ask your `desk.usage(days)` and put the table in `elements.place`, in place of what was there.

```ts
usageTable(document: Document, usage: readonly Day[], days: number, now: Date, prices: Prices): HTMLTableElement
new Dashboard(desk: Desk, prices: Prices, elements: DashboardElements)
dashboard.show(days: number, now?: Date): Promise<void>
```

The tests show you which of their cases pass, but not what they gave or expected. Checks then test what the dashboard needs before it ships.
