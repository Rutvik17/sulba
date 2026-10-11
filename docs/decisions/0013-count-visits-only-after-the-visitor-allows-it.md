# 13. Count visits only after the visitor allows it

- Status: accepted
- Date: 2026-10-10

## Context

The architecture plan chose Cloudflare Web Analytics for visit counts, because it sets no cookies. It was turned on for sulba.dev in its default mode, where Cloudflare adds its script to every page, so every visit was counted without asking. The founder wants every visitor's consent before anything is counted, wherever they live, and suggested a line in the Terms or the Privacy Policy. Under the GDPR such a line isn't consent: consent needs a clear, affirmative choice.

## Decision

On a visitor's first visit, a small panel asks "Can we count your visit?" with Allow and Don't allow, the same size and weight. Cloudflare's script loads only after Allow, from `AnalyticsChoice.astro`. The answer is kept in the browser as `sulba:analytics`, and Privacy choices in the footer asks again. Web Analytics is set to "Enable with JS Snippet installation", so Cloudflare adds nothing. Its token is public and comes from the `WEB_ANALYTICS_TOKEN` repository variable, on main only.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Cloudflare adds the script to every page (its default) | Nothing to build | Counts everyone without asking |
| The same, leaving out visitors in the EU | Nothing to build | Still asks no one, and counts the rest without consent |
| A consent line in the Terms or the Privacy Policy | No prompt on the page | Not consent under the GDPR (Evidence) |
| No analytics until launch | Nothing collected, no prompt | No visit counts at all |
| Ask first, load the script after Allow | Consent from everyone, as the founder asked | A panel on each visitor's first visit, and fewer visits counted |

## Evidence

- The EDPB's [Guidelines 05/2020 on consent](https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-052020-consent-under-regulation-2016679_en) (4 May 2020):
  - "If consent is bundled up as a non-negotiable part of terms and conditions it is presumed not to have been freely given" (p. 7).
  - Scrolling or swiping "will not under any circumstances satisfy the requirement of a clear and affirmative action" (p. 19, example 16).
- Cloudflare's [Web Analytics set-up](https://developers.cloudflare.com/web-analytics/get-started/): Manage site offers "Enable, excluding visitor data in the EU", "Enable with JS Snippet installation" and "Disable".
- What Web Analytics records: its [dimensions](https://developers.cloudflare.com/web-analytics/data-metrics/dimensions/) are country, host, path, referrer, device type, browser and operating system. Its [data collection](https://developers.cloudflare.com/web-analytics/data-metrics/data-origin-and-collection/) page adds timing metrics, from `static.cloudflareinsights.com/beacon.min.js`. Cloudflare's [announcement](https://blog.cloudflare.com/free-privacy-first-analytics-for-a-better-web/) says it uses no "client-side state, like cookies or localStorage, for the purposes of tracking users".

## Why

Only an actual choice is consent, and the founder wants consent from everyone. Asking before loading anything meets that with the analytics already chosen. The panel doesn't block the page, and both answers take one click. The strongest case against it is that most visitors will dismiss or ignore the panel, so the counts will undercount.

## Consequences

- Visit counts cover only visitors who allow them.
- Every first visit shows the panel until it's answered, and blocked storage means asking again on each page.
- Without JavaScript, nothing is counted.
- A changed answer holds from the next page, because a script already running on a page can't be stopped.
- The Privacy Policy gives consent as the legal basis for visit counts.

## Revisit when

A lawyer's review before launch advises differently, or the site needs measurements that a consent-based count can't give.
