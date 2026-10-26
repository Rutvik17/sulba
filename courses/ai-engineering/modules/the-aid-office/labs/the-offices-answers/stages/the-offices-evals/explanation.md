Given three passages instead of five, the model reads {% $fig.prompt_three %} prompt tokens on average rather than {% $fig.prompt_five %}, {% $fig.saved %} fewer. The question's page is among the passages for {% $fig.shown_five %} of the {% $fig.questions %} questions with five, and for {% $fig.shown_three %} with three.

| Release | Right | Wrong | Staff |
| --- | --- | --- | --- |
| five | {% $fig.right_five %} | {% $fig.wrong_five %} | {% $fig.staff_five %} |
| three | {% $fig.right_three %} | {% $fig.wrong_three %} | {% $fig.staff_three %} |

With three, the share of replies that cite only other pages changes by {% $fig.wrong_change %} points, with a margin of {% $fig.wrong_margin %} points at {% $fig.confidence %}, from the questions' differences, each of the {% $fig.pages %} pages' questions counted together. That interval leaves out 0: the questions the two releases were asked are unlikely to explain the change. The share right changes by {% $fig.right_change %} points, with a margin of {% $fig.right_margin %}, an interval that holds 0. A wrong answer costs a student more than a reply from staff, so the office keeps five passages.

Your `answer` passes a reply to staff when it says `I don't know` anywhere. The model often says so after an answer that cites passages: {% $fig.hedged %} of the five's replies do. Had only a reply that says nothing else gone to staff, they would have reached students, and {% $fig.hedged_wrong %} of them cite only other pages.

An outcome goes by the page a reply cites, not by what it says: a reply that cites the question's page can still get its answer wrong, and another page can hold the answer too. It tells two releases apart on the same questions. What the replies say, the office learns by reading them.
