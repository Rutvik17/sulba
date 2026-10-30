# 58. Word the consent page like the authorization screens people know

- Status: accepted
- Date: 2026-10-30
- Amends: [56. Tell the person where an agent's answer goes, and refuse addresses that aren't safe](0056-tell-the-person-where-an-agents-answer-goes.md)

## Context

Decision record 56 made the consent page lead with where answering sends the person, set apart from the rest, in its own words: "Answering sends you to an app on this computer, at 127.0.0.1:33418. Allow it only if you just connected an agent here. An agent chooses its own name, so this is how to tell who is asking." The founder read the page as something no real product would ship. It explained itself rather than asking a question, called pressing Allow "answering", and set its permissions in one paragraph. It also gave no way to switch accounts, and put Allow before Deny, where every dialog in the app puts the safe choice first.

## Decision

The page keeps record 56's behaviour: it leads with where the agent returns the person, and refuses an address that is neither an app on their computer nor a website on HTTPS. Its words and layout change:

- Its heading is "Connect Claude Code to Sulba", with "Signed in as ada@example.com." and a Use another account button, which signs out and comes back to the request.
- A box set apart names the agent and "Returns you to 127.0.0.1:33418 on this computer", or to the app that opens `cursor://` links, or to the website's host. Below it is one condition: "Only allow this if you just started connecting Claude Code on this computer", or on that website or from that app.
- Two short lists follow: "It will be able to" and "It won't be able to", one action a line, then a note that it works in every workspace with the person's role and can be disconnected in Settings.
- The buttons are Cancel, then Allow.
- A refused address reads "This agent can't be connected. It asked to return you to http://agent.example/callback. Sulba only returns you to an app on this computer or to a website over HTTPS."

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Heading, account, a box with the agent and where it returns you, then lists of what it can and can't do, Cancel and Allow (chosen) | Reads like GitHub's, Google's and Supabase's own screens, keeps the destination first, and states the condition for allowing once | Longer than a single paragraph |
| Keep record 56's wording | Already tested | Reads as an explanation of how the page works rather than a question |
| GitHub's layout, with "Authorizing will redirect to …" under the buttons | Familiar | Puts the one fact that tells the person who is asking last, which record 56 decided against |

## Evidence

- [GitHub Docs, Authorizing GitHub Apps](https://docs.github.com/en/apps/using-github-apps/authorizing-github-apps), opened 2026-10-30, with its screenshot of the authorization page: rows of what the app can do, "Cancel" then "Authorize Octo App", and "Authorizing will redirect to https://github.com" under them.
- [Google, Brand verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification), opened the same day, with its figure of the consent screen: "[Display Name] wants access to your Google Account" with the account under it, "Make sure you trust [Display Name]", and "Cancel" then "Allow".
- [Vercel, Consent page](https://vercel.com/docs/sign-in-with-vercel/consent-page), opened the same day: "Two actions: **Allow** or **Cancel**".
- [Supabase, Getting Started with OAuth 2.1 Server](https://supabase.com/docs/guides/auth/oauth-server/getting-started), opened the same day, and the source of Supabase's OAuth consent block: rows for "Client", "Redirects to" and "Signed in as", and "Allow access only if you recognize this application."
- [MCP, Authorization security considerations](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations), opened the same day: authorization servers "**MUST** clearly display the redirect URI hostname during authorization" and "**SHOULD** display additional warnings for `localhost`-only redirect URIs".
- [MCP, Security best practices](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices), opened the same day: a consent page must "Clearly identify the requesting MCP client by name" and "Show the registered `redirect_uri` where tokens will be sent".
- The end-to-end tests in `apps/web/e2e/agents.spec.ts` check the box's words for an agent on this computer and one on claude.ai, the refused address, Cancel, and switching accounts.

## Why

Each screen people already trust asks a question in its heading, shows who is signed in, lists what the app may do in a line apiece, and gives Cancel and Allow, with the destination shown by the buttons or the rows. Following that shape makes the page read as a product's rather than an essay, and the box keeps record 56's point: the address is the one fact a registrant can't dress up, and the condition beside it is the warning the MCP specification asks for when an agent returns to the person's own computer.

The strongest case against it is that a condition the person reads past protects less than one they must act on, such as typing the agent's address. No screen the evidence covers asks that, and an agent allowed by mistake is disconnected in Settings.

## Consequences

- The page's words are part of Sulba's security, and its end-to-end tests check them.

## Revisit when

Supabase supports Client ID Metadata Documents or verified clients, as record 56 says, or people still allow agents they didn't start.
