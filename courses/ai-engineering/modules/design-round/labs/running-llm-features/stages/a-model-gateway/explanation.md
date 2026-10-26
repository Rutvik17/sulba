## What it must do

Give the company one place where every model call is made, so that it can see and limit what each team spends, keep products running when a provider fails, and do it without slowing calls down.

## One interface

Teams call the gateway as they call a provider, with the same request shape and a key of their own. The gateway holds the providers' keys, so a key never sits in a team's code, and a team's key can be turned off without touching anyone else's.

## Cost by team

Every call is logged with its team, product, model, tokens in and out, and cost at that day's prices. The bill splits by team and product, and each team sees its own spending against its budget, with a warning before it runs out.

## Limits

Each team has a rate limit and a spending limit of its own. Batch work, which can wait, has a lower-priority limit of its own, so it uses what the products leave over rather than starving them. A call over a limit is refused at once with the reason, not queued without end.

## Outages

For each model it calls, a team names the fallbacks it has tested. On an error or a timeout, the gateway retries with a growing wait, then sends the call to the next fallback, and the answer says which model gave it. Calls that need one model in particular, for a fixed test set, say, don't fall back.

## Caching

About {% $fig.repeat_share %} of calls repeat a recent request. An exact-match cache, keyed by the whole request, model and settings included, answers repeats without a call, for at most {% $fig.cache_saving %} of last month's bill. It's on only for teams whose requests have one right answer, such as a classification, with an expiry the team sets. A chat answer, or one at a high temperature, isn't cached.

## Privacy

The logs keep counts, costs, models and errors. A request's text is kept only where its team turns that on, for debugging or evals, and only for a set time.

## Speed

{% $fig.calls_day %} calls a day, {% $fig.peak_rps %} a second at most, is light work for a stateless service run on a few machines behind a load balancer. Its own work on a call, the checks of key and limits and the log line written afterwards, is held to {% $fig.overhead_ms %} milliseconds, and answers stream through as they come.

## The follow-up questions

- **The main provider is down:** calls retry, then go to each team's fallbacks, and the dashboard shows which teams have none. Those teams' calls fail fast with the provider's error, rather than hang.
- **A batch job takes the limit:** it moves to the batch limit, which yields to product calls, and its team sees the calls the gateway held back.
- **Out-of-date cached answers:** shorten that team's expiry, or turn the cache off for requests whose answers depend on data that changes.
