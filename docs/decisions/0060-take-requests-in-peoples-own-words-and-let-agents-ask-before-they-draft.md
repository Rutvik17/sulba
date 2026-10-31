# 60. Take requests in people's own words, and let agents ask before they draft

- Status: accepted
- Date: 2026-10-30

## Context

Record 59 takes someone from a request to proven software, with the agents they bring. Its first step is the request: the person says what they want built, an agent asks what it needs to know, then drafts specs for them to approve. Until now a spec was the only thing a person could write in Sulba, and writing one well, with acceptance criteria a test can check, takes an engineer. Someone who wants "an app that books classes at my gym" can't start there, and an agent that drafts from a few sentences has to guess what they meant.

## Decision

- A workspace keeps **requests**: what someone wants built, in their own words, each with a number, REQ-3, a title and Markdown text. A member writes one from the Requests page.
- Agents ask **questions** about a request with `ask_question`, through the MCP server, while it's open. Each question keeps who asked it and, for an agent, the name it registered. Only people answer, in Sulba, so an agent can't answer its own questions. My work shows the questions on the open requests a person wrote.
- An agent drafts specs from a request with `create_spec`, naming it. Each spec drafted from a request links back to it, and the request lists them. They are reviewed and approved as any spec is (record 52).
- A request is **Open** while it's being worked out, **Planned** once a person agrees its specs are the plan, and **Closed** when it won't be built. Only people write or change a request, or move it between these. No questions are asked once it's planned, and no specs are drafted from a closed one.
- Agents read requests with `list_requests` and `get_request`, and the server's instructions give them the order: read the request, ask what they need to know, and draft its specs once they've been answered.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Requests, with questions agents ask and people answer (chosen) | The person's words, the questions and the answers stay as the record of what was meant; an agent drafts from answers, not guesses; works with any agent over MCP | A round trip per question, which the person sees only when they come back to Sulba |
| Agents draft specs straight from the person's words | Fastest | The agent fills every gap with a guess, and nothing records what the person meant |
| A chat between the person and the agent in Sulba | Familiar from app builders | Sulba would have to run the agent, or relay a live conversation it can't hold over MCP; the record is a transcript, not answers |
| People write specs themselves, as before | Nothing to build | Leaves out everyone who can't write a testable criterion |

## Evidence

- Record 59's evidence: Kiro, Lovable and Factory each plan before they build, with a person approving the plan, and the MCP Tasks extension names "human approvals" among the operations a server waits on.
- `packages/data/supabase/tests/requests.test.sql` checks that a viewer can't write a request, that numbers aren't given twice, that an agent asks but can't answer, write or change a request, that a spec drafted from a request names it and can't name another workspace's, that no question is asked of a request that isn't open nor any spec drafted from a closed one, and that people outside the workspace see none of it.

## Why

Each product in record 59's evidence puts a step between what someone says and what gets built, where the request is worked out and a person agrees to it. Sulba's version keeps that step as records rather than a conversation: the person's words, each question and its answer, and the specs that came from them. That lets a reviewer, or the person months later, see why a spec says what it says, and it fits agents that come and go over MCP rather than one Sulba runs.

The strongest case against it is speed: a person who isn't watching Sulba leaves an agent waiting. My work puts the questions waiting on a person first, and an agent can carry on with other work until they're answered.

## Consequences

- Two more tables, `requests` and `questions`, join the daily database check, and the Privacy Policy covers them.
- `create_spec` takes an optional request, so its signature changed.
- Agents learn of an answer only by reading the request again.

## Revisit when

Agents need to ask during building, not only before drafting, or people want to ask each other questions on a request.
