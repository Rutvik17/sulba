# 51. Let coding agents work through an MCP server, signed in by Supabase's OAuth server

- Status: accepted, amended by [56. Tell the person where an agent's answer goes, and refuse addresses that aren't safe](0056-tell-the-person-where-an-agents-answer-goes.md)
- Date: 2026-10-28

## Context

Agents build a team's software from its specs (decision record 46), so an agent has to read a spec and its criteria, see what the tests prove, and write the specs and criteria it is asked to draft. The agents teams use, among them Claude Code, Codex, Cursor and GitHub Copilot in VS Code, take tools from MCP servers, and each signs in to a remote one with OAuth. An agent acts for a person, so it must reach only what that person can, and some decisions, such as approving a spec, have to stay with people. Sulba has to stay on Cloudflare Workers' Free plan and Supabase's free plan, with no key for a person to copy into an agent.

## Decision

- **Server:** Sulba's MCP server answers at `/mcp` on the site's Worker, built with the official TypeScript SDK, `@modelcontextprotocol/server`. Its `createMcpHandler` serves the current protocol revision, 2026-07-28, with no handshake, and falls back to the 2025 revisions' `initialize` for agents that speak them. It keeps no session between requests, and refuses a request from a browser page on another site with 403.
- **Signing in:** Supabase's OAuth 2.1 server signs agents in, with the authorization code flow, PKCE and dynamic client registration. `/.well-known/oauth-protected-resource/mcp` names it, as RFC 9728 describes, and `/mcp` answers a request without a valid token with 401 and that address. Supabase sends the person to `/app/oauth/consent`, which names the agent and what it may and may not do, and answers with Allow or Deny. An agent allowed before goes straight back.
- **Checking a token:** the Worker checks the token against the project's published keys, its issuer, its audience `authenticated` and ES256 or RS256, and takes it only when it carries a `client_id`, so a browser session's token isn't taken. It then asks Supabase's Auth server whether the token's session is still there.
- **Acting:** each tool calls the Data API with the agent's own token, so row-level security sees its person and Postgres sees, from `client_id`, that an agent is acting. There are eight tools: `list_workspaces`, `list_specs`, `get_spec` and `get_evidence` read, and `create_spec`, `update_spec`, `add_criterion` and `reword_criterion` write. Their answers are Markdown text, and a refusal comes back in Postgres's words.
- **Limits:** Postgres refuses an agent's change to a workspace, its members, invitations or repositories, the removal of a criterion, the confirmation of a reworded criterion's tests, a spec's move to approved, abandoned or superseded, and closing its person's account. The same triggers apply whether the agent asks through `/mcp` or calls the Data API itself.
- **History:** each change an agent makes is in its spec's history as the agent's, with the name its OAuth client registered, kept with the change.
- **Disconnecting:** Settings → Agents gives each agent's setup and lists the agents a person has connected; Disconnect revokes the grant, which ends the agent's sessions and refresh tokens. The access functions every policy uses return nothing for an agent whose session is gone, and `/mcp` answers it with 401, so a disconnected agent reaches nothing at once, though its token lasts until it expires.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Supabase's OAuth 2.1 server (chosen) | Built into the project Sulba already uses, on every plan at no charge; dynamic client registration and PKCE, which MCP clients use; tokens row-level security already understands; grants a person can list and revoke | In beta; no custom scopes; tokens can't be bound to `/mcp` as their audience |
| An authorization server in the Worker, such as Cloudflare's `workers-oauth-provider` | Tokens bound to the server, with scopes of Sulba's own | A second store of grants and tokens, kept in KV, and a second sign-in to keep beside Supabase Auth |
| A key a person makes in Settings and pastes into the agent | Simple for any agent | A long-lived secret on every machine, to rotate and to leak; MCP clients sign in with OAuth |
| The official TypeScript SDK's `createMcpHandler` (chosen) | Serves 2026-07-28 and the 2025 revisions on one endpoint; runs on workerd; no state to keep | One more dependency to keep current |
| Cloudflare's `agents` package | Made for Workers; its own `createMcpHandler` wraps the same SDK server, and `McpAgent` keeps sessions in Durable Objects | A larger package around the same SDK, for sessions a stateless server doesn't keep |
| A JSON-RPC handler written for Sulba | No dependency | The protocol's two eras, its headers and its errors to implement and keep up with by hand |
| Limits in Postgres, from the token's `client_id` (chosen) | Hold for any client and any path to the data, the Data API included | Each new table that people alone may change needs its trigger |
| Limits in the MCP server's tools alone | Simpler triggers | An agent's token reaches the Data API too, which would bypass them |

## Evidence

- [Supabase, OAuth 2.1 Server](https://supabase.com/docs/guides/auth/oauth-server): no separate charge; access tokens are the project's JWTs with a `client_id` claim, so row-level security applies to them.
- [Supabase, Getting started with OAuth 2.1 Server](https://supabase.com/docs/guides/auth/oauth-server/getting-started): in beta and on all plans; the authorization path, dynamic registration and the consent page that calls `getAuthorizationDetails` and approves or denies.
- [Supabase, OAuth flows](https://supabase.com/docs/guides/auth/oauth-server/oauth-flows): the token's claims, among them `aud` `authenticated`, `client_id` and `session_id`; tokens last an hour by default; OAuth access tokens have the same access as a person's own session; no custom scopes; revoking a grant invalidates that client's sessions and refresh tokens at once.
- [Supabase, MCP authentication](https://supabase.com/docs/guides/auth/oauth-server/mcp-authentication) and [Token security](https://supabase.com/docs/guides/auth/oauth-server/token-security): using the server for MCP clients, and row-level security from `client_id`.
- MCP specification [2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28/changelog): no `initialize` handshake, the protocol version and capabilities in each request's `_meta`, `server/discover`, and the `Mcp-Method` and `Mcp-Name` headers; [versioning](https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning): a modern client fails against a legacy-only server and a dual-era server serves both; [Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http): the Origin check and its 403; [authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization): protected resource metadata, audience validation, and dynamic client registration kept for authorization servers without Client ID Metadata Documents. The 2025-11-25 revision's [authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization) and [transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) pages for the older agents.
- [RFC 9728, OAuth 2.0 Protected Resource Metadata](https://datatracker.ietf.org/doc/html/rfc9728).
- [@modelcontextprotocol/server](https://www.npmjs.com/package/@modelcontextprotocol/server) 2.4.0, published on 2026-10-23, Apache-2.0: `createMcpHandler`, documented in its types as serving 2026-07-28 with stateless 2025-era serving as the fallback, and `requireBearerAuth`.
- Cloudflare: [Workers limits](https://developers.cloudflare.com/workers/platform/limits/), 10 ms of CPU a request and 50 subrequests on the Free plan; the Agents SDK's MCP [transport](https://developers.cloudflare.com/agents/model-context-protocol/transport/), [authorization](https://developers.cloudflare.com/agents/model-context-protocol/authorization/) and [handler API](https://developers.cloudflare.com/agents/model-context-protocol/apis/handler-api/) pages.
- Each agent's setup: [Claude Code](https://code.claude.com/docs/en/mcp) (`claude mcp add --transport http`, then `/mcp` to sign in), [Codex](https://developers.openai.com/codex/mcp) (`codex mcp add --url`, then `codex mcp login`), [Cursor](https://cursor.com/docs/context/mcp) (`mcp.json` with a `url`; it signs in with OAuth) and [VS Code](https://code.visualstudio.com/docs/copilot/customization/mcp-servers) (MCP: Add Server, then its trust and sign-in prompts).
- `@supabase/auth-js` 2.118.0, read in its source: `auth.oauth`'s `getAuthorizationDetails`, `approveAuthorization`, `denyAuthorization`, `listGrants` and `revokeGrant`, and the endpoints each calls.
- Measured on 2026-10-28, against a local Supabase with the OAuth server on: an agent registered itself, was allowed on the consent page and drove the built Worker's `/mcp` in workerd, on 2025-11-25 and on 2026-07-28; every tool answered; approving a spec through the Data API with the agent's token was refused with 42501; the history named Claude Code for its five changes; after Disconnect, the same token got 401 from `/mcp` and no rows from the Data API, and its refresh token was refused. In Node.js, a warm tool call spent a median of 2.67 ms of CPU and at most 4.42 ms, `tools/list` a median of 2.75 ms, and the first calls up to 15 ms. `packages/data/supabase/tests/agents.test.sql` runs 30 pgTAP tests.

## Why

Supabase's server makes the agent's token one that row-level security already reads, so an agent reaches what its person can and nothing more, with no second store of grants and nothing to pay. Because such a token reaches the Data API as well as `/mcp`, the limits on what an agent may do are in Postgres, where every path meets them. The SDK's handler serves both protocol eras on one endpoint, which the agents in use today need, and keeps the Worker stateless and within its Free plan.

The strongest case against it is the audience: the MCP specification asks a server to take only tokens issued for it, and Supabase's tokens name the project's API, not `/mcp`. This project's Auth server serves Sulba alone, so a token it issues to a client the person allowed can't have been meant for anyone else, and the server also requires the client's ID, its issuer and a live session. A custom access token hook can set the audience later if the project's tokens ever reach another service.

## Consequences

- The project's OAuth server has to be turned on in the dashboard, with `/app/oauth/consent` as its authorization path and dynamic registration allowed, and its Site URL set to `https://sulba.dev`.
- An agent can do everything its person's role allows on specs and criteria; a narrower grant waits for Supabase's custom scopes.
- Each request to `/mcp` asks Supabase's Auth server about its session, one subrequest more than its tools need.
- A new table that only people may change needs a trigger that refuses agents, and its pgTAP test.

## Revisit when

Supabase supports custom scopes or resource indicators, Client ID Metadata Documents become what agents use by default, or a team asks for an agent that acts without a person, such as one in CI.
