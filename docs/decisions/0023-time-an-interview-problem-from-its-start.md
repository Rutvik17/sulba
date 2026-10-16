# 23. Time an interview problem from its start, with the plan before the code

- Status: accepted
- Date: 2026-10-16

## Context

The AI Engineering course adds coding-interview practice: problems on arrays, strings, hash maps and the like, solved the way a live interview asks for them. Companies give a problem a fixed time, and ask for the approach, its cost and its edge cases as well as the code. A Build stage shows its brief at once, opens its solution after the first run, and keeps no time, so it practises none of this. The practice has to run in the learner's browser like every other stage (decision record 17), and keep nothing new outside it.

## Decision

- **A stage kind:** `problem`, with its own file and tests checked like a Build stage's, and its `minutes` as the time it has.
- **Start:** the brief stays hidden behind Start, which says how many minutes the problem has. The clock runs from then, whether the page is open or not, as an interviewer's does.
- **The plan first:** the learner writes how the code works, what it costs in time and space and the inputs that could break it, and the editor opens once the plan has text. The plan stays in a tab of its own.
- **Help:** the hints open one at a time, as in other stages, and the tests run as often as the learner likes. The explanation and the solution open when the code passes or when the minutes are up.
- **The time:** the clock shows the time against the minutes, and turns red past them. A pass keeps the time the passing code was run, and says it against the minutes: "Solved in 14:32, inside its 20 minutes."
- **Where it's kept:** the start, the plan and the time stay in the browser, under `sulba:problem:` and the stage's id. A pass goes to a signed-in learner's account as any stage's does.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| A Problem stage, timed from Start, with the plan before the code (chosen) | Asks for what interviewers ask for, in their order, in the time they give | A learner who leaves mid-problem comes back to a clock past its minutes |
| Build stages with interview problems | No new kind of stage | The brief shows at once, the solution opens after the first run, and nothing is timed or planned |
| A stopwatch the learner starts and pauses | Fits however long a learner has | An interview's clock doesn't pause, so its time says less about readiness |
| A clock that ends the stage when the minutes are up | Holds the learner to the limit | A learner who runs out of time can't finish the problem, which is where most of the practice is |

## Evidence

- Palantir's phone interviews "typically [last] 20 to 45 minutes each", and "while you do want to think about the high-level design before you write any code, it's good to come up with a simple solution first and then go from there" ([The Phone Interview](https://www.palantir.com/careers/getting-hired/the-phone-interview/)).
- Palantir asks candidates to "think about edge cases and the ways in which your code could break", and, once an algorithm "runs with the optimal theoretical complexity (say, O(n))", to keep thinking about efficiency ([Writing Good Code](https://www.palantir.com/careers/getting-hired/writing-good-code/)).
- Meta's initial screen gives 35 minutes to "solve two coding problems", with "questions that are short enough to explain in a few minutes and to solve in 10-30 minutes". Its advice: "Practice under time pressure", "be able to discuss the big-O complexity of your approaches", and "spend some time figuring out the ideal solution to the question" before writing it ([Preparing for your software engineering interview at Meta](https://www.metacareers.com/blog/preparing-for-your-software-engineering-interview-at-meta/)).
- Anthropic's live interviews are "all you–no AI assistance unless we indicate otherwise", and its take-home assessments are done "without Claude unless we indicate otherwise" ([Guidance on Candidates' AI Usage](https://www.anthropic.com/candidate-ai-guidance), updated 10 July 2025). A Problem stage's workspace has no AI help, as no stage's does.

## Why

The chosen kind practises what the companies' own guidance says they look for: a plan before code, its cost, its edge cases and a working solution inside the time. The clock runs as an interview's does, so its time is one a learner can compare with an interview. Keeping the explanation closed until a pass or the end of the time keeps the attempt the learner's own, and opening it then means no one is left without the answer. The strongest case against: a clock that never pauses penalises a learner who is interrupted, and their time on that problem is lost.

## Consequences

The workspace keeps a state per Problem stage and shows a clock, a plan and a gated explanation that other stages don't have. A problem has one attempt at its time: one started and left reads as over its minutes when the learner comes back. The account keeps a Problem stage's pass, but not its plan or its time.

## Revisit when

Learners come back to solved problems to practise them again, so a problem needs a way to start over; or the account should keep a problem's time across devices.
