# 42. Practise a design round against the clock, marked against a rubric

- Status: accepted
- Date: 2026-10-26

## Context

The Intermediate level's interview practice includes a design round: the learner is given a broad problem, such as a service for a town's poll, and designs it in conversation, with no code. Every stage so far passes on tests, and no test can pass or fail a design written in prose. The practice has to run in the learner's browser like every other stage, and Sulba runs no model that could read the design on its behalf (decision record 17). A Problem stage already times an interview problem from its start (decision record 23).

## Decision

- **A stage kind:** `design`, with no file, packages, starter, solution, tests, checks or chart. `stage.yaml` gives its `minutes`, its follow-up `questions`, its `rubric`, each point with what a strong design says to it, and `pass`, how many points pass it. Its brief, hints, explanation, figures and cards are a stage's usual files.
- **Start:** the brief stays hidden behind Start, which says how many minutes the stage has. The clock runs from then, whether the page is open or not, until the answers are in.
- **The design, then the questions:** the learner writes the design and hands it in, and only then sees the follow-up questions, as an interviewer asks them of the design they've heard. The design is fixed once it's in. The learner answers every question and hands the answers in.
- **The rubric:** the rubric then shows each point with its answer, and the explanation opens with the model design. The learner marks each point Met or Not met against what they wrote, each starting as Not met, so a point counts only when the learner claims it. The stage passes when the points met reach `pass`.
- **Again:** an attempt that falls short starts again, with the clock from zero and the design written before, to change. The explanation stays open.
- **Where it's kept:** each attempt's design, answers, time and marks stay in the browser, under `sulba:design:` and the stage's id. A pass goes to a signed-in learner's account as any stage's does, so the account and the database need nothing new.
- **Where it runs:** in the browser only, so a lab that runs on the learner's machine has none. A lab whose stages are all Design stages loads no Python.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| A Design stage the learner marks against a rubric (chosen) | Practises the round's order and its time, and shows what a strong design says to each point | The marks are the learner's own, so a generous marker passes a weak design |
| A Problem stage whose design is code, such as an API's types | Tests check it like any stage | A design round asks for parts, scale and trade-offs, which no test can check |
| A model marks the design | Marks the learner can't bend | Sulba runs no model (decision record 17); a model on the learner's machine needs a machine lab, which has no clock, and its marks of free prose would need checking of their own |
| Multiple-choice questions on a given design | Checked exactly | Practises recognising a design, not making one |

## Evidence

- Meta's design interview "is 45 minutes long. These almost never involve coding. Instead, you'll spend the interview talking and drawing on the whiteboard", and "your interviewer will ask you a very broad design problem and evaluate your solution". Its advice: "Start with requirements"; "a good solution compares and contrasts different approaches. It explores the tradeoffs present in any complex engineering problem and it makes intelligent, reasoned decisions about those tradeoffs"; and "Make it a conversation: Be sure to ask clarifying questions. But make sure you drive towards a good solution" ([Preparing for your software engineering interview at Meta](https://www.metacareers.com/blog/preparing-for-your-software-engineering-interview-at-meta/)).
- Palantir looks for "the ability to tackle technical challenges that are open-ended in nature, with multiple possible solutions that will incur different trade-offs", and advises: "When discussing an open-ended problem in an interview, articulate the alternatives and trade-offs, but don't forget to be pragmatic enough to be able to arrive at some concrete approach. Deliver a functioning idea first, then expand it afterwards" ([Navigating Open-Ended Questions](https://www.palantir.com/careers/getting-hired/navigating-open-ended-questions/)).
- Decision record 17 keeps every run and every model on the learner's device, and decision record 23 times a Problem stage from its start.

## Why

The chosen kind follows the round as the companies describe it: a broad problem, a design with its requirements and trade-offs, then the interviewer's questions of it, in a fixed time. A rubric with an answer to each point gives the learner what an interviewer's feedback would, and showing the questions only after the design is in keeps the design the learner's own. Marking needs no model and no server, so it runs where every stage runs. The strongest case against: a learner who marks generously passes without the skill, and nothing on the page can tell.

## Consequences

The workspace has a third kind of attempt, with its own state, and a pass that rests on the learner's word rather than on tests. The account keeps a Design stage's pass, but not its design, answers or marks, so another device shows the stage done with the rubric alone. A rubric's points have to be specific enough to mark Met or Not met from what a learner wrote.

## Revisit when

Learners want their designs on every device, or a model that marks prose reliably can run in the browser.
