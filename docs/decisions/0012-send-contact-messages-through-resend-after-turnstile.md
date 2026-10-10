# 12. Send contact messages through Resend, after a Turnstile check

- Status: accepted
- Date: 2026-10-10

## Context

The contact form, record 1's route that holds secrets, has to deliver a visitor's message to the studio's inbox. The inbox's address may not appear in any page, and the form must cost nothing. sulba.dev's mail is hosted by iCloud Mail, so the domain's MX records point there. Forms that send email draw bots.

## Decision

The Worker route `/api/contact` takes the message and verifies its Cloudflare Turnstile token with Cloudflare. It then sends the message through Resend's API from an address on sulba.dev, with the writer as the reply-to. The inbox's address, the sender and both secret keys are Worker secrets. Only Turnstile's site key reaches the browser, and the Turnstile script loads when the form is first used.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Resend's API, from the Worker (chosen) | Already the planned sender for sign-in emails; free up to 3,000 emails a month and 100 a day; one HTTPS call | Each message passes through Resend, which keeps it for 30 days; one more secret |
| Cloudflare Email Service's send binding | Free for sends to a verified address, needs no API key, and the message stays with Cloudflare | It sends only from routing domains, so sulba.dev's mail would have to move from iCloud to Cloudflare Email Routing |
| A hosted form service | No server code | Another company receives every message |
| A mailto link | Nothing to build | Puts the address in the page for scrapers, and depends on the visitor's mail app |

For bots, Turnstile is free and verified on the server, and most people see no puzzle. A hidden honeypot field is easy for bots to learn to skip, and rate limiting alone can't tell a person from a bot.

## Evidence

- [Resend's pricing](https://resend.com/pricing) and its [send email API](https://resend.com/docs/api-reference/emails/send-email).
- Cloudflare Email Service's [pricing](https://developers.cloudflare.com/email-service/platform/pricing/), [limits](https://developers.cloudflare.com/email-service/platform/limits/) ("You can only send from your routing domains") and [domain configuration](https://developers.cloudflare.com/email-service/configuration/domains/), whose Email Routing records sit on the root domain and can't be used with external mail servers.
- Turnstile's [server-side validation](https://developers.cloudflare.com/turnstile/get-started/server-side-validation/): a token has at most 2048 characters, can be used once and lasts 300 seconds.
- Turnstile's [test keys](https://developers.cloudflare.com/turnstile/troubleshooting/testing/) and its [plans](https://developers.cloudflare.com/turnstile/plans/): unlimited challenges and up to 20 widgets on the free plan.

## Why

Resend already sent sulba.dev's mail for the old site, and it's the planned sender for sign-in emails, so the form adds no new company. Its free tier covers a contact form many times over. Cloudflare's Email Service would keep the message with Cloudflare, but only by moving the domain's mail away from iCloud. The strongest case against the choice is that every message passes through Resend and stays there for 30 days.

## Consequences

- Before the form can send, the founder sets four Worker secrets (`RESEND_API_KEY`, `CONTACT_TO`, `CONTACT_FROM`, `TURNSTILE_SECRET_KEY`) and the repository variable `TURNSTILE_SITE_KEY`. Until then the form answers 503 and sends nothing.
- The Privacy Policy names Resend and Turnstile as processors of a message.
- Previews build with Turnstile's test key. The production secret rejects test tokens, so a preview can't send mail.
- Tests stand in for `/api/contact` and Turnstile. Only requests the endpoint turns down before calling anyone reach the real one.

## Revisit when

Cloudflare lets a domain whose mail is hosted elsewhere send to its own verified address, or the form outgrows Resend's free tier.
