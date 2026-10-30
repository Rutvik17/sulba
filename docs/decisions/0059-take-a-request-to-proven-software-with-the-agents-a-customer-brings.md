# 59. Take a request to proven software with the agents a customer brings

- Status: accepted
- Date: 2026-10-30
- Amends: [46. Make Sulba where a team specifies its software, agents build it and its tests prove it](0046-make-sulba-where-software-is-specified-built-by-agents-and-proven.md)

## Context

Record 46 made Sulba the place where an engineering team keeps its specs, hands them to its coding agents and proves them with its tests. The founder wants it to reach further: someone with only a request, such as "I want an iOS app that books classes at my gym", comes to Sulba, Sulba works out what they need, specialised agents build it to engineering practice, and the code and its documents end up in one place. The founder named xAI's Grok Bot, Meta's Muse and OpenAI's dots as the kind of agents that would do the work.

Two constraints hold. Sulba's bill stays at $0 until customers pay, and record 46 turned down an app builder because every prompt costs tokens. And the agents named are personal assistants: each runs on its vendor's computer and is reached by messaging it.

## Decision

- Sulba takes a request through five steps, each one a record that people and agents share:
  1. **Request:** the person says what they want built, in their own words.
  2. **Specs:** an agent asks the person what it needs to know, then drafts specs from the request, each with acceptance criteria a test can check, and the person approves them. Nothing is built from a spec no one approved.
  3. **Tasks:** approved specs are split into tasks, each with a role: building, reviewing, testing or writing documents. Record 46 already describes tasks.
  4. **Evidence:** the work lands in the customer's repository, its CI proves each criterion (record 50), and a person approves the release.
  5. **Delivery:** the repository, with documents Sulba assembles from the specs, decisions and evidence.
- The customer brings the agents. Any agent that can connect to a remote MCP server signs in to Sulba as the customer does today (record 51), reads the request and its tasks, and reports back. That includes Claude Code, Codex, Cursor, Muse Code and Grok Bot. Sulba calls no agent and no model itself, so it holds no model keys and pays for no tokens or machines.
- People approve twice: the specs before work starts, and the release once its criteria are proven. Agents never approve, as record 51 already enforces.
- Agents Sulba provides itself, on its own models and machines, come later, as a paid plan, once customers' payments cover them.
- Record 46's rule on names stands: Sulba never calls itself a software factory.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Customers' own agents take their work from Sulba over MCP (chosen) | Costs Sulba nothing per task; works with any agent that connects to a remote MCP server; builds on the MCP server and sign-in Sulba has | The customer needs an agent and its subscription, and the work is only as good as their agent |
| Sulba sends work to vendors' agents through their APIs, such as Devin's or Cursor's | Sulba controls the whole run | Sulba would hold the customer's keys, and each vendor is an integration of its own; Grok Bot, Muse and dots document no way to send them work and get the result back |
| Sulba runs its own agents on hosted models and machines | One experience, with the models Sulba chooses | Every task costs tokens and machine time, which record 46 ruled out at $0 |
| Send work over A2A, the cross-vendor protocol for agents | A standard, now at version 1.0 under the Linux Foundation's Agentic AI Foundation | None of the agents named documents support for it |

## Evidence

- [xAI, Grok Bot overview](https://docs.x.ai/grok-bot/overview) and [Computer and apps](https://docs.x.ai/grok-bot/computer-and-apps), opened 2026-10-30: "You work with a Bot by messaging it", and "A Bot can also add an MCP server that isn't in the catalog, by URL or by a command that runs on its computer". Its webhook starts a run, but a result appears only in the Bot's chat.
- [xAI, Grok Bot FAQ](https://docs.x.ai/grok-bot/faq), opened the same day: "Grok Bot comes with **Premium**, **Super**, and **Ultra** on The X Subscription".
- [Meta, Introducing Muse](https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent/), opened the same day: "Muse runs on Muse Secure VM", reached in the Muse app or WhatsApp, with no developer interface named. [Muse Code, Extending](https://dev.meta.ai/docs/muse-code/extending): Muse Code, Meta's coding agent, connects to MCP servers over streamable HTTP, and "A remote server can require an OAuth 2.1 sign-in."
- [OpenAI, dots](https://developers.openai.com/codex/dots), opened the same day: "You reach the same dot in ChatGPT, Slack, Teams, or a call", and a dot "can use supported plugins installed and enabled for your account". The page documents no way for another platform to send it work.
- [Kiro, Specs](https://kiro.dev/docs/specs/), [Lovable, Chat mode](https://docs.lovable.dev/features/chat-mode) and [Factory, Missions](https://docs.factory.com/missions/overview), opened the same day: each plans before it builds, with a person approving the plan. Kiro writes requirements, a design and tasks, and Lovable uses "Plan mode when you want a structured plan to review and approve".
- [GitHub Docs, Review Copilot's output](https://docs.github.com/en/copilot/how-tos/copilot-on-github/use-copilot-agents/review-copilot-output), opened the same day: approving an agent's own pull request "won't count toward the required number."
- [MCP, Tasks extension](https://modelcontextprotocol.io/extensions/tasks/overview), opened the same day: "Some operations — CI pipelines, batch processing, human approvals — take seconds, minutes, or longer. MCP Tasks let servers return a durable handle instead of blocking".
- [A2A specification](https://a2a-protocol.org/latest/specification/), version 1.0.0, opened the same day: agents publish a card at `/.well-known/agent-card.json` and take work through `SendMessage`.
- [Apple Developer Program](https://developer.apple.com/programs/), opened the same day: "$99 annual membership". [GitHub-hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) and [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions), opened the same day: macOS runners are "free and unlimited on public repositories", and $0.062 a minute beyond a plan's included minutes on private ones. An iOS app is built on the customer's Apple membership and in their CI.

## Why

The products people already use for this, Kiro, Lovable and Factory, all agree on the shape: a plan someone approves before building, then work, then review. Sulba already holds the parts that make that shape trustworthy: specs with criteria a test can check, CI evidence for each one, and approval that agents can't give. Taking a request through the same records makes Sulba's difference the result itself: the customer gets software proven to do what they agreed, rather than what a prompt produced.

Letting the customer's agents pull their work over MCP keeps Sulba at $0 and fits how every agent in the evidence already works: they are MCP clients. It is also the only route the named agents allow. Grok Bot and Muse Code can connect to Sulba as they are, and dots and Muse can join when their vendors document a way.

The strongest case against it is that a customer with only a request may have no agent to bring, and the experience depends on agents Sulba doesn't control. The first answer is that these agents come with subscriptions people buy for other reasons: Grok Bot comes with The X Subscription's Premium, Super and Ultra plans. The second is a paid plan with Sulba's own agents, once revenue pays for them.

## Consequences

- Requests, tasks with roles, and delivery each get a record of their own when they're built, as specs, evidence and agents did.
- A customer's code and secrets stay in their own repository and CI. Sulba holds the request, specs, tasks and evidence, which the Privacy Policy and Terms must cover before the first customer.
- Agents that take work from Sulba need MCP tools for requests and tasks, and decision record 51's limits extend to them.

## Revisit when

A customer can't find an agent to bring, or a vendor of a named agent documents a way for platforms to send it work.
