# 63. Run Sulba's own agents and charge each team for what they use

- Status: accepted
- Date: 2026-11-02

## Context

Record 59 takes a request through specs, tasks, evidence and delivery, and records 60 to 62 built those steps. It left the work to agents the customer brings, so that Sulba's bill stays at $0, and named the condition that would reopen it: a customer who can't find an agent to bring. A company with only a request, such as an assistant for a stadium's finance team, has no coding agent to connect and no repository whose CI sends test results.

The founder decided on 2026-11-02 that Sulba runs the agents itself and pays their model bill, as products sold to companies do, and charges each team for what its work uses. Sulba has no revenue yet, so the bill comes out of the founder's pocket until a working prototype raises money, and every run has to be capped.

## Decision

- Sulba's own agents do each step of record 59, each a role with its own instructions:
  - **Intake** reads a request and asks its writer what it needs to know.
  - **Architect** drafts the specs from the request and the answers, each with acceptance criteria a test can check.
  - **Planner** splits each approved spec into tasks with roles (record 61).
  - **Builders**, one per task and in parallel, write the code and its tests in the request's repository and open a pull request each.
  - **Reviewer** reviews each pull request against the criteria its task covers.
- People keep the decisions: they answer the questions, approve the specs (record 52), mark tasks done, and approve the release (record 62). Sulba's agents act as agents do today: Postgres refuses them what it refuses any agent (record 51).
- Sulba pays the model bill and records what each run cost. A workspace has a monthly limit that only Sulba sets, no run starts once the workspace has reached it, and each run carries its own cap.
- Teams pay for what their runs use. How Sulba prices that and takes payment gets a record of its own before the first team pays; until then the limit is the only control.
- A team that has its own coding agents can still connect them over MCP (record 51), and their work counts the same.
- The Academy doesn't change: its labs still run on the learner's device, and Sulba runs no model for them (record 17).

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Sulba runs its own agents, pays the model bill and charges each team for its usage, with limits (chosen) | Anyone with a request gets software, with no agent or CI of their own; one experience Sulba controls | Sulba pays for every run before it is paid, so limits have to hold from the first run |
| Keep customers' own agents only (record 59) | Costs Sulba nothing | A company with only a request can't use it, which is the customer the founder wants to pitch to |
| Sulba runs the agents on the customer's own model account | No model bill for Sulba | Every customer needs an account and a key with a model provider before their first request, and Sulba holds their keys |

## Evidence

- [Lovable, Credits and usage](https://docs.lovable.dev/introduction/plans-and-credits), opened 2026-11-02: "Lovable uses one credit balance for building your app, chatting with Lovable, hosting your app and running its built-in backend (Cloud), and powering AI features in your deployed app", and "workspace owners and admins can cap how many credits a member, project, or the whole workspace can use, and get alerted when usage or the remaining balance crosses a threshold."
- [Replit, AI billing](https://docs.replit.com/billing/ai-billing), opened the same day: "Replit AI features use usage-based billing", and for the models behind its agent, "Agent handles these integrations automatically — no API keys or setup required. You're billed at the provider's public API rate".
- [Devin, Self-serve plans](https://docs.devin.ai/admin/billing/self-serve), opened the same day: plans carry "A daily and weekly usage quota that covers Devin sessions", with "Pay-as-you-go on-demand credits for usage past your quota", which "are shared across the whole team."
- [Factory, Individual plans](https://docs.factory.ai/pricing), opened the same day: usage is governed by "rolling Rate Limits", with "Extra Usage: prepaid credits", and "If a Mission hits a Rate Limit, it pauses."
- [Claude API, Rate limits](https://platform.claude.com/docs/en/api/rate-limits), opened the same day: an organization can set "your own spend limit below your tier’s cap to control costs", and requests past it are refused.

## Why

Every product a company would compare Sulba with holds the model bill itself and sells usage, by credits, quotas or the provider's rate, with limits per workspace or member: Lovable, Replit, Devin and Factory all do. A company that asks for software expects to pay for the work, not to set up a model account first. Sulba's difference stays what record 59 made it: the request ends in specs a person approved, criteria the tests prove, and a release a person signed off.

The strongest case against it is the bill: one founder pays for every run until revenue comes. Three caps answer it, each tighter than the last: the spend limit on Sulba's model account, each workspace's monthly limit, and each run's own cap.

## Consequences

- Sulba holds a model provider's API key as a Worker secret. Without it, the routes that start agents answer 503, as the contact form does without its secrets.
- What a team writes in a request, its answers and its code go to the model provider that runs the agents; the Privacy Policy says so before the first run.
- Record 59's rule that Sulba calls no model and no agent no longer holds for the app. Its five steps and two approvals stand.
- Which runtime runs the agents is record 64.

## Revisit when

A team is ready to pay, which needs the pricing record, or the model bill outgrows what the limits allow.
