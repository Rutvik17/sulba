A team's assistant has {% $fig.conversations %} conversations a day. A teammate has written a new prompt that makes answers shorter, and better on the {% $fig.tried %} examples they tried. The last prompt change raised complaints by {% $fig.complaint_rise %}, and nobody noticed for {% $fig.noticed_days %} days.

Design how a prompt change gets from a teammate's laptop to every user: what it's tested on, how it's released, and how it's stopped. Take these as given:

- the team's test set has {% $fig.questions %} questions, each scored from {% $fig.low %} to {% $fig.high %};
- between two prompts, a question's score changes with a standard deviation of about {% $fig.sd %};
- a gate tests at a level of {% $fig.alpha %} with a power of {% $fig.power %}, as in Regression gates.
