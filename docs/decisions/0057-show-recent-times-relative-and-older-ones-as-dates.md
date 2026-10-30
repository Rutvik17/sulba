# 57. Show recent times as how long ago, and older ones as dates

- Status: accepted
- Date: 2026-10-30

## Context

The app shows when things happened: when a spec was updated, when a run reported, when someone joined, when an invitation link expires. Each page formatted them itself, in the browser's own language, so a German browser put German dates in an English app. A date always carried its year ("Sep 15, 2026"), an invitation's expiry read like any other date, and a time stayed "just now" until the page reloaded. Only some of them showed the full time on hover.

## Decision

- Every time the app shows goes through one component, `When` (`apps/app/src/When.tsx`), which renders a `<time>` with its `datetime` and the full date and time on hover, such as "Tue, Oct 27, 2026 at 9:41 PM GMT+1".
- Something that happened in the last 30 days says how long ago it was: "just now", "5 minutes ago", "3 hours ago", "yesterday", "6 days ago". From 30 days on it gives the day.
- A day is "Oct 27" this year and "Oct 27, 2025" in any other. Days that aren't events in a feed, such as when someone joined, when an agent was connected, when a spec was created and when an invitation link expires, always show as a day.
- Dates are in English, as the app is, ordered as the first English locale the browser names orders them (en-GB gives "27 Oct"), in the person's time zone.
- Times on the page move on by themselves: one clock ticks every 30 seconds while a time is showing.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Recent times as how long ago, older ones and fixed days as dates (chosen) | Reads at a glance for activity, exact where exactness matters, and matches GitHub, Atlassian and Shopify | Two formats to learn, and the hover is the only way to the exact time of a recent one |
| Every time as how long ago | One format | "in 5 days" for an expiry hides the day it stops working, and "8 months ago" is vaguer than a date |
| Every time as a full date and time | Exact, and works the same for screen readers | Dense tables of "Oct 27, 2026, 9:41 PM" are hard to scan, and recency, which is what activity is read for, takes working out |

## Evidence

- [Primer, RelativeTime guidelines](https://primer.style/product/components/relative-time/guidelines), opened 2026-10-30: "< 1 minute: just now", then relative up to a month, then "on Nov 18", and "on Nov 18, 2021" in a past year. "Don't use relative dates for future specific dates." "Use precise dates when the user needs to know the exact time of past dates." It prefers long forms ("2 months ago") to micro ones ("2mo").
- [Primer, RelativeTime accessibility](https://primer.style/product/components/relative-time/accessibility), opened the same day: the `title` tooltip "is not accessible to keyboard users".
- [github/relative-time-element](https://github.com/github/relative-time-element), its README, opened the same day: `threshold` defaults to `P30D`, "a relative date phrase is used for up to a month and then the actual date is shown".
- [Atlassian Design System, Date and time](https://atlassian.design/foundations/content/date-time), opened the same day: "You should always provide a way for people to see the actual timestamp, usually via a tooltip."
- [Shopify, Grammar and mechanics](https://shopify.dev/docs/apps/design/content/grammar-and-mechanics), opened the same day: "Less than 1 min: Just now", "Yesterday at 10:30 am", "More than 1 year: Aug 14, 2016", and dates and times joined with "at" rather than a comma.
- `apps/app/src/format.test.ts` pins each form, from "just now" to "Dec 24, 2025", the hover's form, and the English locale chosen from the browser's languages.

## Why

Activity is read for recency, and every source agrees that a phrase like "3 hours ago" reads faster than a time in a table, as long as the exact time is one step away. Past a month the phrase gets vague, so the date takes over at the same point GitHub uses. A day that isn't activity, and above all an expiry, is a fact people act on, and Primer advises against a relative phrase for a future date. Formatting in English keeps dates in the language of the page around them, and taking the order from the person's English locale keeps "27 Oct" for those who expect it.

The strongest case against it is Primer's: a `title` tooltip doesn't reach keyboard users. The tables' times aren't interactive, so a tooltip that takes focus would add a tab stop to every row; the exact time stays in each `<time>` element's `datetime` for software that reads it.

## Consequences

- A page that shows a time uses `When`, and a test that checks one asserts its `datetime` or its words, not a date with a year that will change.
- The clock re-renders every time on the page twice a minute while one shows.

## Revisit when

The app is translated, or people ask to see exact times in its tables.
