# 56. Tell the person where an agent's answer goes, and refuse addresses that aren't safe

- Status: accepted
- Date: 2026-10-30
- Amends: [51. Let coding agents work through an MCP server, signed in by Supabase's OAuth server](0051-let-coding-agents-work-through-an-mcp-server-signed-in-by-supabase.md)

## Context

Agents sign in with dynamic client registration (decision record 51), so anyone can register an OAuth client, with any name and any address to send the person's answer to. Supabase's dashboard says so when registration is turned on: "Bad actors could create malicious apps with legitimate-sounding names to phish your users for authorization."

The attack runs on sulba.dev itself. Someone registers a client named "Claude Code" with a return address on their own website, then sends a person Supabase's authorization link for it. The person lands on Sulba's own consent page, which used to lead with the agent's name and mention the address last, in small text: "Either way, you go back to …". If they press Allow, Supabase sends the authorization code to that website. There the registrant, who made the PKCE verifier, exchanges it for a token that acts for the person, within decision record 51's limits.

The name proves nothing. The address does: an agent on the person's computer waits at a loopback address or opens links of its own scheme, and an agent on the web waits at an HTTPS address on its own domain.

## Decision

- `destinationOf` in `packages/data/src/agents.ts` sorts a request's return address into one of three kinds:
  - an app on the person's computer, at a loopback address (`localhost`, `127.0.0.1` or `[::1]`) over HTTP
  - an app that opens links of its own scheme, such as `cursor:`
  - a website, by its host, over HTTPS
- Every other address is refused: plain HTTP to another computer, an address with a user name or password in it, `javascript:`, `data:`, `vbscript:`, `blob:`, `file:` and `about:`, and anything that isn't an address.
- The consent page leads with where answering sends the person, set apart from the rest: "Answering sends you to an app on this computer, at 127.0.0.1:33418. Allow it only if you just connected an agent here. An agent chooses its own name, so this is how to tell who is asking." For a website it names the host and says to allow it only if the person just connected an agent there.
- A refused address gets "This request can't be allowed" and no Allow or Deny, so the page never sends anyone there. A request allowed before is checked the same way before the page sends the person back.
- Dynamic registration stays on. Decision record 51's limits are unchanged: an agent can't change a workspace's people, repositories or settings, or approve a spec, and the person can disconnect it at once.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Lead with where the answer goes, and refuse unsafe addresses (chosen) | The person sees the one fact a registrant can't fake to them; the page never sends anyone to plain HTTP elsewhere or a script; the agents teams use keep connecting | A person can still allow a website they don't recognise |
| Turn dynamic registration off, and register each agent by hand | No one can register a client | MCP clients such as Claude Code register themselves (decision record 51), so each team would wait for Sulba to register its agent first |
| Allow only addresses on the person's computer | Phishing through a website ends | Agents that run on the web, such as claude.ai's connectors, couldn't connect |
| Keep a list of known agents' addresses, and warn about the rest | Known agents look trusted | The list would always be behind, and a registrant can still copy a known agent's name |

## Evidence

- Supabase's dashboard, when dynamic OAuth app registration is turned on: "Dynamic OAuth apps (also known as dynamic client registration) exposes a public endpoint allowing anyone to register OAuth clients. Bad actors could create malicious apps with legitimate-sounding names to phish your users for authorization." The founder quoted it on 2026-10-30.
- [Supabase, Model Context Protocol (MCP) Authentication](https://supabase.com/docs/guides/auth/oauth-server/mcp-authentication), read through Supabase's documentation search on 2026-10-30:
  - Its security considerations: always require explicit approval, show clear information about what the agent can access, give an option to deny access, and let people revoke access later.
  - Dynamic registration is how MCP clients register themselves.
- [Supabase, Getting Started with OAuth 2.1 Server](https://supabase.com/docs/guides/auth/oauth-server/getting-started), read the same way: its example consent page shows the client's name and its redirect URI.
- `@supabase/auth-js`'s types, read in this repository's `node_modules`: a request's details give the client's ID, its name, website and logo as the client registered them, and "the OAuth client's registered redirect URI".
- `packages/data/src/agents.test.ts` covers the three kinds of address and eight refused ones, among them `http://localhost.example`, `http://127.0.0.1.nip.io` and an HTTPS address with a password in it. The end-to-end tests cover an agent on this computer, one on claude.ai and a refused one.

## Why

On sulba.dev's own page, a registrant chooses the name, website and logo the person reads, but the address their answer goes to is the one the client registered, and the code goes nowhere else. It is the one fact on the page a registrant can't dress up as someone else's. Leading with it, and refusing the addresses no real agent needs, makes the decision rest on that fact. The agents teams use keep working, and decision record 51's limits still bound what an allowed agent can do.

The strongest case against it is that a person in a hurry may allow a website they don't recognise. The page says plainly when to allow one, and an agent allowed by mistake is disconnected in Settings, with its changes in each spec's history.

## Consequences

- An agent whose registered return address is plain HTTP to another computer can't be allowed.
- The consent page's wording is part of Sulba's security, and its end-to-end tests check it.
- Spam registrations still appear in the project's list of OAuth clients. Clearing ones never used is left for when the list needs it.

## Revisit when

Supabase supports Client ID Metadata Documents or verified clients, which name an agent by an address it controls, or a team asks to allow only the agents it chooses.
