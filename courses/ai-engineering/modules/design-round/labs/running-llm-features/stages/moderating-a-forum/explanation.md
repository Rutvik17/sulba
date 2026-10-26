## What it must do

Keep posts that break the rules out of sight from the moment they're made, without hiding so many good posts that the volunteers can't keep up or members stop posting.

## Hide, then decide

The model doesn't remove anything. It hides a post it scores above a threshold, and a volunteer decides. A wrong hide costs its writer a wait, which a volunteer can undo. A post the model misses is left for members to report, as now.

## The threshold

Of {% $fig.posts %} posts a day, about {% $fig.bad_share %} break the rules: {% $fig.bad %} posts. At a recall of {% $fig.recall %} the model hides {% $fig.caught %} of them, and at a precision of {% $fig.precision %} those are {% $fig.precision %} of all it hides, so it hides {% $fig.flagged %} posts a day, {% $fig.wrongly %} of them wrongly. That fits the volunteers' {% $fig.capacity %} posts a day. A higher recall would hide more, and more of them wrongly, past what the volunteers can review, so the threshold is set where the hidden posts fit their day.

## Measuring

Precision and recall come from posts the volunteers labelled, as in Measuring a classifier, never from the model's own view of itself. Recent posts join the labelled set every month, since what members write, and how they break the rules, changes.

## Reasons and appeals

The model names the rule a post seems to break, from the forum's list, and the volunteer and the member both see it. A member can appeal a hidden post. A volunteer other than the first decides, and each decision, either way, becomes a labelled post.

## New tricks

Members who are hidden try new spellings and new phrasings. The volunteers' decisions bring those into the labelled posts, and every change of prompt or model is checked against them before it ships, so a fix for one trick doesn't undo another.

## Timing

A post is checked as it's made, with a time limit. A post whose check doesn't finish in time is shown and checked afterwards, so the forum never stops because the model is slow.

## The follow-up questions

- **How many to hide:** as many as the volunteers can review. With these numbers, {% $fig.flagged %} a day at a recall of {% $fig.recall %} fits their {% $fig.capacity %}.
- **Misspelled words:** volunteers' decisions add the new spellings to the labelled posts, which the next prompt is checked against. Members' reports catch what the model misses in the meantime.
- **An unfair hide:** the member appeals, a second volunteer decides, and the decision joins the labelled posts.
