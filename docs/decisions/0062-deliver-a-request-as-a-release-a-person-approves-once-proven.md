# 62. Deliver a request as a release a person approves once it's proven

- Status: accepted
- Date: 2026-10-31

## Context

Record 59 ends with two steps: a person approves the release once its criteria are proven, and the customer gets the repository with documents Sulba assembles from the records. Records 60 and 61 built the steps before them, so a request now has its questions, the specs drafted from it, their tasks and pull requests, and the tests that prove each criterion (record 50). Nothing yet says a request is delivered, who said so, or what was true when they did, and a customer who asked in their own words has nothing to read but the app's pages.

## Decision

- A request has **releases**: release 1, 2 and on, each approved by a person with an optional note. A request can have several, as the work it asked for grows.
- A release can be approved only when the request is open, at least one spec drafted from it still counts (not abandoned or superseded), every such spec is approved or implemented, each has criteria, and every criterion is proven by the latest run of each suite (record 50). Postgres checks this when the release is approved and says what is missing, and the request's page lists the same before anyone tries.
- Only people approve a release, and one member's approval is enough. Agents read releases but never approve one, as they never approve a spec (records 51 and 59).
- A release keeps what was true when it was approved: each spec's number, title and status, each criterion's text and how many tests proved it, and each task that wasn't canceled, with its pull request. Later changes to the specs don't change it, nobody can edit it, and it goes only when its workspace does.
- Each release has a document in Markdown, written from what it keeps and from the request: what was asked, the questions answered about it, and each spec with how its criteria were proven and the pull requests that built it. Members download it from the request's page, and agents read it with `get_release`, so an agent can add it to the customer's repository.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Releases a person approves once every criterion is proven, each keeping what was proven (chosen) | One record of who delivered what and on what evidence; the document can't drift from it | The customer's deploy stays in their CI, which Sulba doesn't run |
| Mark a request done when its specs are | Nothing to build | No one is named as having signed it off, and later changes to the specs rewrite what was delivered |
| Approve deployments through GitHub environments' required reviewers | Built into the customer's CI | Ties delivery to GitHub's paid plans for private repositories, and the approval knows nothing of the request, its specs or their criteria |

## Evidence

- [GitHub Docs, Managing environments for deployment](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments), opened 2026-10-31: a team can "specify people or teams that must approve workflow jobs that use this environment", "Only one of the required reviewers needs to approve the job for it to proceed", and "to prevent users from approving workflows runs that they triggered, select Prevent self-review". On GitHub Free, Pro and Team, required reviewers "are only available for public repositories".
- [GitHub Docs, Automatically generated release notes](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes), opened the same day: they "include a list of merged pull requests, a list of contributors to the release, and a link to a full changelog."
- Record 59's evidence: approving an agent's own pull request on GitHub "won't count toward the required number."

## Why

GitHub's own release gate is the shape teams already know: a named person approves, one approval is enough, and the one who started the work can be kept from approving it. Sulba keeps that shape and checks what GitHub's gate can't see: that every spec drafted from the request was approved, and that the tests prove each of its criteria. Refusing agents is Sulba's form of preventing self-review, as an agent did the work.

Release notes from GitHub list pull requests. A Sulba release says more, because it starts from the request: what the customer asked, what they answered, and which tests prove each thing they were promised. Keeping it as it was when approved means the document still describes what was delivered after the specs move on.

The strongest case against it is that a release in Sulba isn't a deploy, and a team may approve one and never ship it. The customer's deploy belongs to their CI, where their secrets are; Sulba records the decision and its evidence, and an agent can check `get_release` before it deploys.

## Consequences

- `releases` joins the daily database check, and the Privacy Policy covers it.
- The request's page shows its delivery, and agents have `get_release`.

## Revisit when

Customers want Sulba to start their deploy, or a release needs more than one person's approval.
