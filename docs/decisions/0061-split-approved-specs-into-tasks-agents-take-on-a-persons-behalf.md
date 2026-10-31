# 61. Split approved specs into tasks that agents take on a person's behalf

- Status: accepted
- Date: 2026-10-30

## Context

Record 59's third step is tasks: approved specs split into work an agent can take, each with a role. Record 46 described a task as work sized for an agent, with what it needs and its definition of done, and said agents take tasks and report back through the MCP server. Today an agent can read an approved spec and build it, but nothing records who is building what, whether two agents are on the same spec, which pull request holds the work, or that an agent is stuck.

## Decision

- A workspace keeps **tasks**: TASK-7, each drafted from one approved spec, with a title, a role, Markdown instructions, and the spec's criteria it covers. The roles are **Build**, **Test**, **Review** and **Document**.
- Members and agents write tasks, and only from an approved or implemented spec, so nothing is built from a spec no one approved (record 59). A task a person writes covers all its spec's criteria; an agent names the ones it covers.
- A task is **Open**, then **In progress** once someone takes it, **Blocked** when its taker can't go on and says why, **In review** once its pull request is named, and **Done** or **Canceled**.
- An agent takes a task for its person, as Linear's agents are delegated an issue: the task names the person and the agent, and the person stays answerable for it. One taker at a time: a task already taken can't be taken again until it's released. A member can move on a task someone else holds, such as releasing one an agent left; an agent moves only its own person's.
- Each task names one pull request, in one of the workspace's repositories, as GitHub's coding agent opens one pull request per task. The repository's CI then proves the criteria the task covers (record 50).
- Only people mark a task done, cancel it or open it again, as only people approve a spec. An agent takes, blocks, resumes, releases and hands in a task.
- My work shows the tasks in review and the blocked tasks on the specs a person owns; a spec's page lists its tasks; and agents use `list_tasks`, `get_task`, `create_task`, `take_task` and `update_task`.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Tasks in Sulba that agents take and hand in over MCP (chosen) | One record from spec to pull request to evidence; works with any agent; people keep the last word | Teams that plan in a tracker see the work in two places until Sulba keeps in step with it (record 46) |
| Let agents work straight from approved specs | Nothing to build | Two agents can build the same spec, nobody sees who is stuck, and no pull request is tied to its criteria |
| Create issues in the customer's tracker and let its agent integrations take them | Uses tools teams have | Ties Sulba to each tracker's API and its agents' terms, and Sulba loses the link from criteria to work |

## Evidence

- [Linear, Agents: Getting Started](https://linear.app/developers/agents), opened 2026-10-30: agents "can be @mentioned, delegated issues through assignment", and "Assigning an issue to your app now sets it as the delegate, not the assignee—so humans maintain ownership while agents act on their behalf."
- [Linear, Developing the Agent Interaction](https://linear.app/developers/agent-interaction), opened the same day: "Session states let the user know if the agent is currently working, waiting for user input, in an error state, or has finished work", with the states "pending, active, error, awaitingInput, complete, stale", and an agent shows its pull request by adding its URL to the session.
- [GitHub Docs, About GitHub Copilot coding agent](https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent), opened the same day: Copilot "can only work on one branch at a time and can open one pull request per task."
- Record 59's evidence: approving an agent's own pull request on GitHub "won't count toward the required number."

## Why

Linear and GitHub agree on the shape: a person hands an agent one piece of work, the agent says when it's working, stuck or finished, and its result is one pull request that a person reviews. Sulba adds what they don't hold: the work comes from a spec someone approved, names the criteria it must prove, and its pull request's tests become that spec's evidence.

The strongest case against it is that teams already track work, and two lists drift. Record 46 answers it by keeping Sulba in step with the tracker, which comes after this; until then a task is the agent's work order, not the team's plan.

## Consequences

- `tasks` and `task_criteria` join the daily database check, and the Privacy Policy covers them.
- Delivery (record 59's last step) can list each spec's tasks and their pull requests.

## Revisit when

Agents need to split a task into smaller ones, or teams want tasks kept in step with their tracker.
