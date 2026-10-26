## What it must do

Let the team change prompts often, while no change that makes answers worse reaches every user, and any that slips through is caught in hours, not days.

## Prompts as code

A prompt lives in the repository as a file, beside the model name and settings it runs with, and changes by review like code. Every answer logs the prompt version that made it, so a complaint can be traced to the version behind it.

## The gate

Every change runs the test set beside the current release. Each question's two scores are compared in a pair, so each question's own difficulty drops out of the difference, and the change ships only if a one-sided test at {% $fig.alpha %} finds no drop. The {% $fig.tried %} examples the teammate tried are a start, not a test.

## How large a drop the gate can find

With differences of standard deviation {% $fig.sd %} over {% $fig.questions %} questions, the change's standard error is `$\fig{sd} / \sqrt{\fig{questions}}$`, about {% $fig.error %}. At a power of {% $fig.power %}, the smallest drop the gate finds is

```math
\delta = (z_{1 - \alpha} + z_{\text{power}}) \cdot \text{error}
```

about {% $fig.detectable %}. A drop of {% $fig.drop %} needs `$n' = \lceil n (\delta / \text{drop})^2 \rceil$` questions: {% $fig.needed %}.

## The canary

A change that passes the gate goes first to {% $fig.canary %} of conversations, about {% $fig.canary_conversations %} a day. Its feedback, complaints and handoffs are compared with the rest's for a day before it goes to everyone. The canary sees real users' questions, which the test set can only sample.

## Going back

The prompt's version is a setting the service reads at each call. Going back is a change of setting that takes effect in minutes, with no deploy.

## The model behind the name

Calls name a dated model version where the provider offers one, so the model changes only when the team changes it, through the same gate. The test set also runs every day against what's live, so a change behind a name shows within a day.

## After release

A dashboard shows feedback, complaints and handoffs by prompt version, with an alert when one rises past its usual range. The last change took {% $fig.noticed_days %} days to notice. With the alert, it would have been hours.

## The follow-up questions

- **Better on the test set, worse in the canary:** stop the rollout and look at the canary's unhelpful answers. They show what the test set is missing, often a kind of question it doesn't have, and those questions join it.
- **The model behind the name changes:** a dated version doesn't change. Where there's none, the daily run shows the change within a day.
- **A drop of {% $fig.drop %}:** the gate finds drops of about {% $fig.detectable %}, so it would usually miss one of {% $fig.drop %}. Grow the set to {% $fig.needed %} questions, or score several replies to each question, which shrinks the differences' spread.
