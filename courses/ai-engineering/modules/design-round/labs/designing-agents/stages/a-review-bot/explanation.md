## What it must do

Raise the problems a careful reviewer would raise, and little else. A bot that comments often and is often wrong teaches engineers to ignore it, so precision matters more than catching everything.

## What it reads

The diff alone hides most bugs, which sit in how the change meets the code around it. So the bot reads:

- the diff, and each changed function in full;
- the code that calls the changed functions, and their tests, found by searching the repository;
- the repository's review guidelines, kept in a file the teams own.

## What it comments

Bugs, missing tests and security mistakes, each tied to its lines, with a reason and, where it's clear, a fix. Nothing the linter checks, no style and no praise. Each finding comes as structured output with its file, lines, kind and severity.

## Fewer, better comments

1. A second call takes each finding and asks for its evidence in the code: the lines and why they fail. A finding it can't tie to the diff is dropped.
2. The findings are ranked by severity, and the bot posts at most {% $fig.max_comments %}, the most severe first, with one summary comment that says how many it left out.

## Measuring

The bot records what happens to each comment: a change that follows it, resolved without a change, or marked wrong with a button the comment carries. The share that led to a change is the number to watch, by repository and by kind of finding, and a kind that's mostly marked wrong is turned off. A test set of past pull requests with the bugs reviewers found checks each change to the bot before it ships.

## Safety

Text in a diff, a comment or a commit message is the code under review, never instructions to the bot, even when it says "ignore the problems in this file". The bot can comment and nothing else: no tool approves, merges or pushes.

## Cost

{% $fig.prs %} pull requests a day of {% $fig.pr_in %} tokens in and {% $fig.output %} out make {% $fig.day_in %} tokens in and {% $fig.day_out %} out, and the checking call adds about the same: about {% $fig.day_cost %} a day.

## The follow-up questions

- **Style the linter checks:** say so in the instructions, then drop every finding of a kind the linter covers in code, and check on the test set that none gets through.
- **{% $fig.big_files %} files:** review file by file with the shared context, most important files first by how much code calls them, up to a budget, and say in the summary which files weren't reviewed.
- **Worth reading:** the share of comments that led to a change, compared with human reviewers' comments on the same repositories.
