# 20. Schedule review with FSRS, from a log of reviews

- Status: accepted
- Date: 2026-10-15

## Context

Phase 4 brings spaced review: once a learner passes a stage, its main ideas come back as cards, each at the time it's worth recalling again. Review has to work signed out, as the labs do, and follow a signed-in learner from device to device, offline and in late batches, as progress does ([record 18](0018-keep-progress-as-a-log-of-attempts.md)). The browser reaches Supabase directly, each row guarded by row-level security ([record 4](0004-keep-learner-data-and-sign-in-in-supabase.md)), and the bill stays at nothing. Every number a learner sees can be traced to its inputs on the same screen, and that includes when a card comes back.

## Decision

- **Cards:** each stage's `cards.yaml` holds its cards, a question and its answer in Markdoc with the stage's figures, each under a permanent id. The content checks hold them to the same rules as the rest of the prose. A card is due for the first time once its stage is passed.
- **The log:** each answer is a review: the card's id, the learner's rating (Again, Hard, Good or Easy) and when they gave it. The browser keeps every review it records in local storage, signed in or not. Signed in, it sends to an append-only `reviews` table the reviews the account doesn't have yet, and once a visit takes in those made on other devices. Each review's id is made in the browser, so a review sent twice is kept once.
- **The schedule:** the browser replays each card's reviews, in the order they were given, through FSRS-6 as ts-fsrs implements it, with ts-fsrs's defaults: 90% desired retention, learning steps of 1 and 10 minutes, a relearning step of 10 minutes, intervals of at most 36,500 days, and no fuzz. A card is due at its time or, once its interval is a day or more, from the start of that day where the learner is. When nothing else is due, a card in a learning step that is due within 20 minutes shows early. Each rating shows the interval it would give, and each card shows its reviews.
- **Access and limits:** as for attempts. A learner adds and reads only their own reviews; nothing can be changed or removed except by closing the account, which removes it all; and an account can add 2,000 reviews a day. pgTAP tests prove each rule.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| A log of reviews, replayed through FSRS in the browser (chosen) | Works the same signed out; retries, offline batches and two devices merge without losing a review; a new version of FSRS, or parameters fitted later, reschedules every card from its history; Postgres keeps only the log | Each visit replays every card's history, and a signed-in visit reads the account's whole log |
| The browser writes each card's state: its due date, stability and difficulty | One small row per card, and nothing to replay | Two devices that review the same card overwrite each other, as an upserted progress row would (record 18); a schedule can't be recomputed when FSRS changes |
| A log of reviews, with FSRS in Postgres keeping each card's state | The schedule lives in one place, and reads are small | FSRS ported to PL/pgSQL and kept in step with ts-fsrs by hand; signed-out learners still need FSRS in the browser; reviews that arrive out of order need a replay anyway |
| Anki's older scheduler, SM-2 | Simple and widely used | Anki's manual says FSRS determines more accurately how much a learner is likely to forget |
| A fixed schedule, such as reviews after 1, 3, 7, 14 and 30 days | No library and no model | Ignores how each review went: a card the learner keeps forgetting waits as long as one they know |

## Evidence

- In a review of ten learning techniques, "practice testing and distributed practice received high utility assessments because they benefit learners of different ages and abilities and have been shown to boost students' performance across many criterion tasks and even in educational contexts" (Dunlosky et al., [Improving Students' Learning With Effective Learning Techniques](https://doi.org/10.1177/1529100612453266), 2013).
- Students who took recall tests on prose passages retained substantially more after 2 days and after a week than students who restudied them the same number of times, though restudying won after 5 minutes (Roediger and Karpicke, [Test-Enhanced Learning](https://doi.org/10.1111/j.1467-9280.2006.01693.x), 2006).
- A meta-analysis of 839 assessments in 317 experiments found that the gap between study sessions that gives the best retention grows with how long the material must be retained (Cepeda et al., [Distributed Practice in Verbal Recall Tasks](https://doi.org/10.1037/0033-2909.132.3.354), 2006).
- Anki has supported FSRS since 23.10. Desired retention is "the proportion of cards recalled successfully when they are due"; its default of 90% "offers a good balance of retention and workload", and "Above 90% the workload increases very quickly". Learning steps should be shorter than a day and as few as possible, since "repeating a card multiple times in a single day does not significantly contribute to long-term memory". FSRS's optimizer fits parameters to a learner's history and performs poorly on fewer than a few hundred reviews. Pressing Hard on a forgotten card makes "all intervals" "unreasonably high" ([Anki manual: Deck Options](https://docs.ankiweb.net/deck-options.html)).
- Anki shows a card in learning early when there's nothing else to study and it's due within the learn-ahead limit, 20 minutes by default ([Anki manual: Preferences](https://docs.ankiweb.net/preferences.html)). Each answer button shows when the card would come back, and the manual gives what each rating means: Again when the answer was wrong or couldn't be recalled, Hard when it was right with doubt or took long, Good when it took some effort, Easy when it took none ([Anki manual: Studying](https://docs.ankiweb.net/studying.html)).
- In FSRS, stability is the interval at which the probability of recall falls to 90%, and the next interval is the time at which the forgetting curve reaches the desired retention ([The Algorithm](https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Algorithm)).
- On the review histories of 9,999 Anki users, about 350 million reviews, FSRS-6 with parameters fitted to each user predicted recall with a log loss of 0.346, against 0.395 for a constant at the user's average retention, 0.469 for Duolingo's half-life regression and 0.499 for Ebisu; FSRS-7 with default parameters scored 0.362 ([SRS Benchmark](https://github.com/open-spaced-repetition/srs-benchmark)).
- ts-fsrs 5.4.2 implements FSRS-6 under the MIT licence. `repeat` previews all four ratings and `next` applies one, and its defaults are 90% retention, a 36,500-day maximum interval, no fuzz, and learning steps of 1 and 10 minutes with a relearning step of 10 minutes ([ts-fsrs](https://github.com/open-spaced-repetition/ts-fsrs)).

## Why

Retrieval spread over time is among the best-supported ways to keep what was learned, and FSRS is the scheduler Anki ships, measured on hundreds of millions of reviews. Keeping the log rather than each card's state gives review the guarantees record 18 gives progress: reviews are only added, and replaying them in time order gives the same schedule whatever order they arrived in, on every device. A signed-out learner gets the same schedule from their browser's log. The strongest case against: FSRS's parameters are the defaults, fitted to Anki users' own cards rather than to Sulba's learners, until there are enough reviews to fit them.

## Consequences

The Review page carries every card in the courses and loads ts-fsrs, about 13 KB compressed. A ts-fsrs update can move every due date, so it's tested like any change to the schedule. Reviews recorded signed out go to the account the browser next signs in to, as passes do. Fitting parameters to Sulba's learners needs a few hundred reviews each, which the log keeps.

## Revisit when

A learner's log is too long to read or replay on a visit, ts-fsrs ships FSRS-7, or learners have enough reviews to fit parameters to.
