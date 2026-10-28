# 52. Approve specs by named reviewers, and ask them again when a spec changes

- Status: accepted
- Date: 2026-10-28

## Context

A spec is the team's agreement on what to build (decision record 46), and "approved" is the state that says the agreement holds. Until now any member could move a spec to Approved, so the status said someone had clicked it, not who agreed. The product spec gives a spec named approvers and gives each person a My work page that starts with the specs waiting for their review. A spec changes while it's discussed, and an approval of yesterday's text says nothing about today's.

## Decision

- **Reviewers:** a workspace's members name a spec's reviewers while it's a draft or in review, up to 10, from anyone in the workspace, viewers included, but its owner. A reviewer who comes to own the spec, or leaves the workspace, stops reviewing it.
- **Answers:** while the spec is in review, each reviewer approves it or asks for changes, and asking for changes says what to change. A reviewer can change their answer until the spec is approved.
- **Approval:** a spec with reviewers is approved when the last of them approves it, and Postgres refuses to approve it by hand before then. A spec with no reviewers is approved by a member, as before.
- **Change:** a change to a spec's title, text or criteria while it's in review asks those who approved it to review it again, and a spec that goes into review again starts a new round. A request for changes stands until its reviewer answers again; My work shows when the spec has changed since. A member can ask any reviewer again.
- **Agents:** an agent can't name reviewers or review; `get_spec` shows it each answer and what a reviewer who asked for changes said.
- **History:** each request, answer and removal joins the spec's history, and an approval that approves the spec is in it as the reviewer's.
- **My work:** a workspace opens on My work at `/app/<slug>/`: the specs waiting for the person's review, the specs they own that aren't built, with where each review stands, and the criteria failing on their specs.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Named reviewers, approved when all approve, approvals asked again on change (chosen) | The status names who agreed to which version; matches Google Drive's default and GitHub's stale-approval setting | A typo fix in review asks the approvers again |
| Any member approves, as before | Nothing to set up | "Approved" doesn't say who agreed |
| A required number of approvals, from anyone | Fits large teams | Who must agree isn't named, so My work can't tell a person what's theirs to review |
| Keeping approvals across changes | No repeated reviews | An approval of earlier text counts for the spec as it is now |
| Asking again on change, requests for changes too | One rule for every answer | The owner loses the note they're working from the moment they start to edit |

## Evidence

- [GitHub Docs, Pull request reviews](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/about-pull-request-reviews): a reviewer comments, approves or requests changes; reviews are requested from specific people, who need read access.
- [GitHub Docs, About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches): a required number of approvals; a request for changes from someone with admin permissions blocks merging until they approve or it's dismissed; stale approvals can be dismissed when the diff changes.
- [Google Drive Help, Get approvals on files](https://support.google.com/drive/answer/9387535): approvers approve or reject with an optional note; with "Require all approvers to review the same content", edits reset all approvals.
- [Google Drive API, Manage approvals](https://developers.google.com/workspace/drive/api/guides/approvals): all reviewers must approve; any reviewer declining declines the approval; `RESET_APPROVAL`, the default, sets each response back when the file is edited.
- `packages/data/supabase/tests/spec_reviews.test.sql` runs 35 pgTAP tests, among them that one approval leaves a spec in review, that an edit or a reworded criterion asks the approvers again while a request for changes stands, that the last approval approves the spec, that an agent can't review, and that someone outside the workspace sees no reviews.

## Why

Naming reviewers makes Approved mean that particular people agreed, and lets My work show each person what's theirs to answer. Approving only when every reviewer has is the rule both Google Drive and a branch requiring reviews follow, and it needs no number to configure. Asking approvers again when the spec changes keeps every approval about the spec as it is. A request for changes stays because the owner works from it, as GitHub keeps an admin's request for changes until they approve.

The strongest case against it is the cost of small edits: fixing a typo in review asks the approvers again. That's the price of each approval being about the same text, and asking again is one press for them.

## Consequences

- A spec that has been approved and is edited stays approved; its history shows what changed after.
- Reviewers learn they've been asked from My work alone until the Inbox and its notifications.
- A new table that holds review state joins `database-check.yml`.

## Revisit when

A team asks for a number of approvals instead of named reviewers, for reviewers set by code owners, or for an approved spec to go back into review when it changes.
