# 64. Run Sulba's agents on Claude Managed Agents

- Status: accepted
- Date: 2026-11-02

## Context

Record 63 has Sulba run its own agents: Intake, Architect, Planner, a Builder per task and a Reviewer. Each needs a model, a loop that calls tools, and for building, a machine where it can clone a repository, run the tests and push. Sulba runs on a Cloudflare Worker, which answers requests but runs no long jobs and no containers, and on Supabase. One founder builds and pays for it, so the runtime has to cap what each run spends and say what it cost, and the agents must never hold a key that can change Sulba's data.

## Decision

- Each role is an agent on Claude Managed Agents, defined in Sulba's code with its model, instructions and tools. The Worker creates it once and updates it when its definition changes, so each run records the agent's version.
- Each step is one session, started by the Worker. Intake, Architect, Planner and Reviewer each write one JSON document to the session's outputs, and an outcome grades it against a rubric drawn from the step's rules before it counts. Sulba reads the document when the session finishes and writes the questions, specs, tasks or review itself, through the same Postgres functions people use. The agents never hold a Sulba token.
- Builders work in parallel, one session per task. Each mounts the request's repository, writes the code and the tests that name the criteria it covers, pushes a branch and opens a pull request. The repository's CI sends its results to Sulba (record 50), so the tests, not the agent, prove each criterion.
- Sulba keeps one private repository per request, in a GitHub organization of Sulba's, with Sulba's CI step already in place, until the team takes it over. Sulba's GitHub token goes to the session as the repository's token, which stays outside the sandbox.
- Every session starts with a budget: the role's cap, or what is left of the workspace's monthly limit if that is less. Anthropic's webhooks tell the Worker when a session changes state, and the Worker records each run's cost from the session's usage.
- Every role runs on Claude Opus 5.5, with the effort set per role: low for Intake, high for the rest.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Claude Managed Agents (chosen) | Anthropic runs the loop and a sandbox per session; hard budgets per session; the cost of each session, to bill from; outcomes graded against a rubric; webhooks a Worker can take | In beta, and transcripts stay with Anthropic until Sulba deletes them |
| Claude Agent SDK in GitHub Actions, one job per task | Runs Claude Code's loop in the repository's own CI | Sulba writes the dispatching, the metering and the spend caps itself |
| Sulba's own loop on the Messages API, with a sandbox from another provider | Full control over every call | Sulba writes and runs the loop, compaction and sandboxes, and pays a second vendor |

## Evidence

- [Claude Managed Agents overview](https://platform.claude.com/docs/en/managed-agents/overview), opened 2026-11-02: a "Pre-built, configurable agent harness that runs in managed infrastructure. Best for long-running tasks and asynchronous work." On data retention: "Sessions are stateful resources; transcripts persist until you delete them."
- [Pricing, Claude Managed Agents](https://platform.claude.com/docs/en/about-claude/pricing), opened the same day: "billed on two dimensions: tokens and session runtime", tokens at model rates, and runtime at "$0.08 USD per session-hour", which "accrues only while the session’s status is `running`." Claude Opus 5.5 is $4 per million input tokens and $20 per million output tokens.
- [Session budgets](https://platform.claude.com/docs/en/managed-agents/budgets), opened the same day: "A session budget is an optional hard spend ceiling", and the session object carries "`usage.list_cost`", "the session’s consumed list cost".
- [Define outcomes](https://platform.claude.com/docs/en/managed-agents/define-outcomes), opened the same day: "When you define an outcome, the harness automatically provisions a *grader* to evaluate the artifact against a rubric. The grader uses a separate context window to avoid being influenced by the main agent’s implementation choices." Output files go to "`/mnt/session/outputs/`".
- [Multiagent orchestration](https://platform.claude.com/docs/en/managed-agents/multiagent-orchestration), opened the same day: "Agents can act in parallel with their own isolated context".
- [Accessing GitHub](https://platform.claude.com/docs/en/managed-agents/github), opened the same day: "You can mount a GitHub repository to your session sandbox and connect to the GitHub MCP for making pull requests."
- [Webhooks](https://platform.claude.com/docs/en/managed-agents/webhooks), opened the same day: "Every delivery carries the `webhook-id`, `webhook-timestamp`, and `webhook-signature` headers", signed with a secret "shown only once".

## Why

Managed Agents is the one option where Sulba writes neither the agent loop nor the sandbox, and it brings the two things a founder paying the bill needs most: a hard cap on every session, and each session's cost to bill from. Outcomes fit Sulba's records directly: an artifact graded criterion by criterion against a rubric is how specs are written and checked, and the grader's separate context keeps it from grading its own work. Webhooks let a Worker follow every session without holding a connection open.

Agents that write files rather than call Sulba keep Sulba's data behind its own Postgres functions: an agent can't change a record, only propose one that Sulba checks before writing it.

The strongest case against it is depending on a beta from the model's own vendor. The agents' definitions are plain instructions, tools and rubrics, so moving them to the Agent SDK in CI, the second option, is a change of runner, not of design.

## Consequences

- The Worker holds an Anthropic API key, the webhook signing secret and a GitHub token for Sulba's organization as secrets; without them, the routes that start agents answer 503.
- A request's text, its answers, its specs and its code go to Anthropic, which keeps each session's transcript until Sulba deletes it. The Privacy Policy says so before the first run.
- Each run's cost is Anthropic's list price for it, which is what record 63's limits count.

## Revisit when

Managed Agents leaves beta with changes to sessions or pricing, or a role needs more than one session's budget to finish its work.
