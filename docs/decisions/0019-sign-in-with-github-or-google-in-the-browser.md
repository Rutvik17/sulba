# 19. Sign in with GitHub or Google, in the browser

- Status: accepted
- Date: 2026-10-14

## Context

Accounts keep a learner's progress across devices ([record 18](0018-keep-progress-as-a-log-of-attempts.md)). Every page is built ahead of time ([record 1](0001-render-each-route-the-way-its-content-needs.md)), and the browser reaches Supabase directly ([record 4](0004-keep-learner-data-and-sign-in-in-supabase.md)). The bill stays at $0, and Resend's free plan sends 100 emails a day ([record 12](0012-send-contact-messages-through-resend-after-turnstile.md)). Learners are engineers, and accounts are optional: every lab works without one.

## Decision

- **Providers:** learners sign in with GitHub or Google through Supabase Auth. No emailed codes and no passwords.
- **In the browser:** sign-in uses the PKCE flow. `/sign-in/` sends the learner to the provider and, when they come back, the client trades the code for a session, kept in local storage as `sulba:session`. `/account/` shows who is signed in, signs out of that browser only, and closes the account.
- **Closing an account:** a `security definer` function deletes the caller's own row in `auth.users`, which removes their sessions, identities and everything they recorded.
- **Loading:** only the sign-in and account pages load supabase-js. A lab's workspace loads it only when the browser holds a session, so a learner who never signs in downloads none of it.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| GitHub and Google, with PKCE in the browser (chosen) | No email to send, so no daily cap; the providers handle passwords and two-factor sign-in; pages stay static | A learner with neither account can't sign in |
| Emailed one-time codes | Works for anyone with an email address | Each sign-in is an email, and Resend's free plan stops at 100 a day |
| Passwords | No outside account needed | A reset is an email too, and Sulba would hold credentials to protect against reuse and stuffing |
| Sessions in cookies, read by the Worker | The server knows who is signed in on every request | Personal pages would render in the Worker, against its 100,000 free requests a day, and every page is built ahead of time |

## Evidence

- In the PKCE flow, "The code verifier is created and stored locally when the Auth flow is first initiated", so the code can only be traded in the browser that started the sign-in ([PKCE flow](https://supabase.com/docs/guides/auth/sessions/pkce-flow)). supabase-js trades it as the client starts, when `detectSessionInUrl` is on, its default, and removes the code from the address ([GoTrueClient](https://github.com/supabase/supabase-js/blob/v2.117.3/packages/core/auth-js/src/GoTrueClient.ts)). Its default flow is the implicit one, so the site asks for PKCE.
- The address a provider returns to must match the project's Redirect URLs, where `*` and `**` are wildcards ([Redirect URLs](https://supabase.com/docs/guides/auth/redirect-urls)). The Auth server also lets a sign-in return to the Site URL's own origin and to loopback addresses ([request.go](https://github.com/supabase/auth/blob/master/internal/utilities/request.go)).
- A publishable key is "Safe to expose online", and row-level security decides what it reaches ([API keys](https://supabase.com/docs/guides/api/api-keys)).
- Signing out defaults to every session, "`global` (default) when all sessions active for the user are terminated" ([Sign out](https://supabase.com/docs/guides/auth/signout)); the site signs out of one browser.
- "You may delete users directly", and deleting a row in `auth.users` "does not automatically sign out a user" ([Managing user data](https://supabase.com/docs/guides/auth/managing-user-data)), so closing an account then signs the browser out.

## Why

Sign-in costs nothing at any number of learners, needs no email, and leaves Sulba holding no password. Engineers almost all have a GitHub or Google account, and those who'd rather not use one lose nothing but syncing, since every lab works without an account. Keeping the session in the browser keeps every page static and the Worker out of it. The strongest case against: learners with neither account, or whose employer blocks both, can't keep their progress across devices.

## Consequences

The project's Site URL must be sulba.dev, and each preview's address has to be in its Redirect URLs for sign-in to work there. The project's email sign-in has to be off, so no account can be made without a provider. Accounts come from the providers' own pages, so the Privacy Policy names GitHub, Google and Supabase. Sign-out and sign-in leave the browser's own copy of the learner's code in place.

## Revisit when

Teams need sign-in through their own identity provider, or learners ask for a way in without GitHub or Google.
