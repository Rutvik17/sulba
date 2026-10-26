# 44. Mark a module optional, and leave it out of the next lab until it's started

- Status: accepted
- Date: 2026-10-26
- Amends: [26. Show a course as a map of its modules](0026-show-a-course-as-a-map-of-its-modules.md)

## Context

Intermediate ends with two modules a learner can skip, Go and Java, for programmers who want a second language for services. A course's page (decision record 26) gives every module a numbered row and its level's time, and its card names the next lab: the first lab started but not done, else the first not done after the last one done, else the first not done. With Go and Java at the end of Intermediate, a learner who finishes the capstone would be sent into Go, ahead of the next level, and the level's time would count hours the learner may never spend.

## Decision

- **The file:** `optional: true` in a module's `module.yaml` marks it optional. A module is required unless it says so.
- **The row:** an optional module's row says Optional before its labs and their time, and keeps its number.
- **The level:** its facts say how many of its modules are optional, and give their time apart from the rest: "About 300 hours, and about 60 hours more in the optional modules". Its progress counts every lab, the optional ones too.
- **The next lab:** an optional module's labs count for the next lab only once one of them is started, or when every other lab is done. A lab started but not done is next, in any module, as before.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| A field in `module.yaml`, which the page reads (chosen) | One place says it; the row, the level's time and the next lab all follow from it | One more field, and one more rule for the next lab |
| "Optional" in the module's title | Nothing to build | The level's time and the next lab still treat the module as required, and each author words it their own way |
| Go and Java as a course of their own | Nothing optional inside a level | They build on Intermediate's model API and capstone, so they'd sit apart from the labs they use |
| A field, with optional labs left out of the level's progress | Progress reads as done once the required labs are | Two counts of labs on one level, which a learner can't tie to the rows below |

## Evidence

- The Odin Project, [How this course will work](https://www.theodinproject.com/lessons/foundations-how-this-course-will-work): "Additional resources are the only thing that is considered optional unless explicitly stated."
- Open edX, [Proposal: Optional Content Support](https://openedx.atlassian.net/wiki/spaces/OEPM/pages/6506840085/Proposal+Optional+Content+Support), updated 2 July 2026: authors "use inconsistent workarounds, such as adding 'Optional' to titles", and "Optional content is clearly labeled for learners, excluded from required completion calculations"; a learner needs "to clearly see which content is optional in order to prioritize required coursework".
- Decision record 26's own next-lab rule, which, run on Intermediate with Go and Java last, sends a learner who finishes the capstone to Go.

## Why

A field lets each place the page uses a module, its row, its level's facts and the next-lab card, treat it the same way, where a word in the title changes only what the row says. The next lab is the card a learner follows back in, so it keeps to the required modules until the learner chooses an optional one. The level's progress counts every lab, so its numbers add up from the rows under it. The strongest case against: a learner who has done every required lab still reads, say, "45 of 51 labs done", with the optional ones left.

## Consequences

`courses/README.md` names the field. A module's row and its level's facts read it, and the next lab skips an optional module the learner hasn't started. Sulba has no certificates or completion, so nothing else changes.

## Revisit when

A level has optional labs inside a required module, or learners need a level marked done without its optional modules.
