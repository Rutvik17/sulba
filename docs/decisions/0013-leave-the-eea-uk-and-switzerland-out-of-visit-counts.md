# 13. Leave the EEA, the UK and Switzerland out of visit counts

- Status: accepted
- Date: 2026-10-10

## Context

The architecture plan chose Cloudflare Web Analytics for visit counts, because it sets no cookies (decision record 8). Cloudflare adds its script to sulba.dev's pages as they pass through its network, and settings in the dashboard decide for which visitors. The founder weighed asking every visitor before anything is counted. A line in the Terms or the Privacy Policy wouldn't be consent under the GDPR, so asking meant a prompt on each first visit. The Web Analytics setting already in place, "Enable, excluding visitor data in the EU", leaves visitors in the EU out instead, but not visitors in the UK, where the law asks for a way to object (Evidence).

## Decision

Nothing asks visitors, and nothing about visit counts is in this repository. Two settings in the dashboard decide who is counted:

- Web Analytics stays on "Enable, excluding visitor data in the EU". Cloudflare doesn't add its script for visitors in the EU, and drops what its data centers there collect.
- A Configuration Rule turns on "Disable Real User Monitoring (RUM)" for `(ip.src.country eq "GB") or (ip.src.country eq "NO") or (ip.src.country eq "IS") or (ip.src.country eq "LI") or (ip.src.country eq "CH")`: visitors from the UK, Norway, Iceland, Liechtenstein and Switzerland.

The Privacy Policy names the places whose visits aren't counted.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Enable for every visitor | Counts every visit, with nothing to build | Counts visitors in the EU without asking |
| Enable, excluding visitor data in the EU | Nothing to build or show, and visits from the EU aren't counted | Counts visitors in the UK without the way to object that UK law asks for |
| The same, plus a Configuration Rule for the UK, Norway, Iceland, Liechtenstein and Switzerland | Also leaves out the UK, the rest of the EEA and Switzerland | Visits from those countries aren't counted, and it's a second dashboard setting |
| The same, with the EU's countries listed in the rule too | The EU is left out by the visitor's country, whichever data center serves the visit | 34 more country codes in the rule |
| A consent line in the Terms or the Privacy Policy | No prompt on the page | Not consent under the GDPR (Evidence) |
| Ask every visitor, and load the script after Allow | Consent from everyone, wherever they live | A panel on each first visit, fewer visits counted, and code to keep |
| Disable Web Analytics | Nothing collected | No visit counts |

## Evidence

- Cloudflare's [Web Analytics set-up](https://developers.cloudflare.com/web-analytics/get-started/) describes the setting: "Enable, excluding visitor data in the EU - The JS Snippet will not be injected for visitors from the EU."
- Cloudflare's [changelog entry for the setting](https://developers.cloudflare.com/changelog/post/2025-02-25-rum-exclude-eu/) (26 February 2024) says it drops "requests from visitors in the European Union to comply with GDPR and CCPA", and that "we will drop all metrics collected by our EU data centers automatically". The EU is decided by the data center that serves a visit, not by the visitor's country.
- What Web Analytics records: its [dimensions](https://developers.cloudflare.com/web-analytics/data-metrics/dimensions/) are country, host, path, referrer, device type, browser and operating system. Its [data collection](https://developers.cloudflare.com/web-analytics/data-metrics/data-origin-and-collection/) page adds timing metrics, from `static.cloudflareinsights.com/beacon.min.js`. Cloudflare's [announcement](https://blog.cloudflare.com/free-privacy-first-analytics-for-a-better-web/) says it uses no "client-side state, like cookies or localStorage, for the purposes of tracking users".
- The EDPB's [Guidelines 05/2020 on consent](https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-052020-consent-under-regulation-2016679_en) (4 May 2020): "If consent is bundled up as a non-negotiable part of terms and conditions it is presumed not to have been freely given" (p. 7).
- The UK's [Data (Use and Access) Act 2025, Schedule 12](https://www.legislation.gov.uk/ukpga/2025/18/schedule/12), in force since 5 February 2026, adds Schedule A1 to the PEC Regulations. Under its paragraph 5, a site may gain access to a visitor's device for statistics without consent only if, among other conditions, the visitor "is given a simple means of objecting, free of charge". sulba.dev gives none.
- Cloudflare's [Configuration Rules settings](https://developers.cloudflare.com/rules/configuration-rules/settings/) include "Disable Real User Monitoring (RUM)", which turns Web Analytics off "for matching requests", and "Configuration rules have precedence over any Web Analytics rules". The free plan has [10 rules](https://developers.cloudflare.com/rules/configuration-rules/). The rule matches [`ip.src.country`](https://developers.cloudflare.com/ruleset-engine/rules-language/fields/reference/ip.src.country/), the visitor's two-letter country code.
- Cloudflare's [EU field for rules](https://developers.cloudflare.com/ruleset-engine/rules-language/fields/reference/ip.src.is_in_european_union/) lists 34 codes, the EU's overseas regions among them, and needs a Business or Enterprise plan. On the free plan, the EU's countries can only be listed one by one.
- Checked on 10 October 2026, after the rule was deployed: page views served from Cloudflare's Toronto data center still carry the script. A visit from the five countries can't be tested from Toronto.

## Why

Cloudflare offers its EU setting so that sites can meet the GDPR. In the UK, counting without consent needs a way to object, which sulba.dev doesn't offer, so the rule leaves UK visitors out instead. The founder chose to treat the rest of the EEA (Norway, Iceland and Liechtenstein) and Switzerland the same way. Everyone else reads the site without a prompt. The strongest case against it is that it asks no one: visitors elsewhere are counted without a choice.

## Consequences

- Visits from the EU, the UK, Norway, Iceland, Liechtenstein and Switzerland aren't counted, so the totals undercount Europe.
- Visitors elsewhere are counted without being asked.
- For the EU, Cloudflare goes by its data centers, so a visit from the EU that reaches a data center outside it may be counted.
- Both settings live in the dashboard, so no test checks them, and changing either means changing the Privacy Policy.

## Revisit when

A lawyer's review before launch advises differently, the founder wants consent from everyone (the prompt built in [pull request 18](https://github.com/Rutvik17/sulba/pull/18)), or the site needs counts from Europe.
