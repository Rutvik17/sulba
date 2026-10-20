The current release on the test set, at {% $fig.confidence %}, with a target of ±{% $fig.target %}:

| Line | Share passing every check | Margin | Questions | Needed |
| --- | --- | --- | --- | --- |
| `all` | {% $fig.all_rate %} | ±{% $fig.all_margin %} | {% $fig.all_questions %} | {% $fig.all_needed %} |
| `dmv` | {% $fig.dmv_rate %} | ±{% $fig.dmv_margin %} | {% $fig.dmv_questions %} | {% $fig.dmv_needed %} |
| `ssa` | {% $fig.ssa_rate %} | ±{% $fig.ssa_margin %} | {% $fig.ssa_questions %} | {% $fig.ssa_needed %} |
| `studentaid` | {% $fig.studentaid_rate %} | ±{% $fig.studentaid_margin %} | {% $fig.studentaid_questions %} | {% $fig.studentaid_needed %} |
| `va` | {% $fig.va_rate %} | ±{% $fig.va_margin %} | {% $fig.va_questions %} | {% $fig.va_needed %} |

Over every question, the test set falls short of the target: {% $fig.all_needed %} questions would reach it, where it has {% $fig.all_questions %}. Each service on its own is far from it, and would need {% $fig.fewest_needed %} to {% $fig.most_needed %} questions, where it has {% $fig.dmv_questions %} to {% $fig.va_questions %}. `studentaid` would need more than the {% $fig.studentaid_asked %} questions people asked it in all. Until the help desk has more questions, it reports each service with its wide margin, and decides on the share over every question.

`needed` scales the test set by the square of how far its margin is from the target: halving a margin takes four times the questions. It holds only for questions spread over pages as these are. A test set with fewer questions to a page pulls together less, and needs fewer questions for the same margin.
